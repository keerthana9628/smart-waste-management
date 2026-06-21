from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app import db
from app.models import Bin, BinFillHistory, Alert, log_activity
from app.utils.decorators import admin_required
from config import Config

bins_bp = Blueprint('bins', __name__, url_prefix='/bins')


def _check_and_create_alert(bin_obj):
    """Create an alert if the bin's fill level crosses the threshold and
    there isn't already an unresolved alert for it."""
    threshold = Config.FILL_ALERT_THRESHOLD
    if float(bin_obj.fill_level) >= threshold:
        existing = Alert.query.filter_by(bin_id=bin_obj.id, is_resolved=False).first()
        if not existing:
            alert_type = 'full' if float(bin_obj.fill_level) >= 95 else 'fill_warning'
            alert = Alert(
                bin_id=bin_obj.id,
                alert_type=alert_type,
                message=f'{bin_obj.bin_code} ({bin_obj.location}) has reached '
                        f'{bin_obj.fill_level}% capacity.'
            )
            db.session.add(alert)


@bins_bp.route('/')
@login_required
def index():
    """List all bins with search and filter support."""
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')

    query = Bin.query
    if search:
        query = query.filter(
            db.or_(
                Bin.bin_code.ilike(f'%{search}%'),
                Bin.location.ilike(f'%{search}%')
            )
        )
    if status_filter:
        query = query.filter_by(status=status_filter)

    bins = query.order_by(Bin.fill_level.desc()).all()
    return render_template('bins.html', bins=bins, search=search, status_filter=status_filter)


@bins_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    """Add a new bin."""
    if request.method == 'POST':
        bin_code = request.form.get('bin_code', '').strip()
        location = request.form.get('location', '').strip()
        capacity = request.form.get('capacity_l', 100)
        fill_level = request.form.get('fill_level', 0)
        waste_type = request.form.get('waste_type', 'general')
        latitude = request.form.get('latitude') or None
        longitude = request.form.get('longitude') or None

        if Bin.query.filter_by(bin_code=bin_code).first():
            flash(f'Bin code "{bin_code}" already exists.', 'danger')
            return render_template('bin_form.html', bin=None)

        new_bin = Bin(
            bin_code=bin_code,
            location=location,
            capacity_l=int(capacity),
            fill_level=float(fill_level),
            waste_type=waste_type,
            latitude=latitude,
            longitude=longitude,
        )
        new_bin.update_status()
        db.session.add(new_bin)
        db.session.flush()  # get new_bin.id

        # Record initial history point
        db.session.add(BinFillHistory(bin_id=new_bin.id, fill_level=new_bin.fill_level))
        _check_and_create_alert(new_bin)
        db.session.commit()

        log_activity(current_user.id, 'ADD_BIN', f'Added bin {new_bin.bin_code} at {new_bin.location}')
        flash(f'Bin "{bin_code}" added successfully.', 'success')
        return redirect(url_for('bins.index'))

    return render_template('bin_form.html', bin=None)


@bins_bp.route('/<int:bin_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(bin_id):
    """Edit an existing bin's details and fill level."""
    bin_obj = Bin.query.get_or_404(bin_id)

    if request.method == 'POST':
        bin_obj.location = request.form.get('location', '').strip()
        bin_obj.capacity_l = int(request.form.get('capacity_l', bin_obj.capacity_l))
        bin_obj.waste_type = request.form.get('waste_type', bin_obj.waste_type)
        bin_obj.latitude = request.form.get('latitude') or bin_obj.latitude
        bin_obj.longitude = request.form.get('longitude') or bin_obj.longitude

        new_fill_level = float(request.form.get('fill_level', bin_obj.fill_level))
        level_changed = new_fill_level != float(bin_obj.fill_level)
        bin_obj.fill_level = new_fill_level
        bin_obj.update_status()

        if level_changed:
            db.session.add(BinFillHistory(bin_id=bin_obj.id, fill_level=bin_obj.fill_level))
            _check_and_create_alert(bin_obj)

        db.session.commit()
        log_activity(current_user.id, 'EDIT_BIN', f'Updated bin {bin_obj.bin_code}')
        flash(f'Bin "{bin_obj.bin_code}" updated successfully.', 'success')
        return redirect(url_for('bins.index'))

    return render_template('bin_form.html', bin=bin_obj)


@bins_bp.route('/<int:bin_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(bin_id):
    """Delete a bin and its related records."""
    bin_obj = Bin.query.get_or_404(bin_id)
    code = bin_obj.bin_code
    db.session.delete(bin_obj)
    db.session.commit()
    log_activity(current_user.id, 'DELETE_BIN', f'Deleted bin {code}')
    flash(f'Bin "{code}" deleted successfully.', 'success')
    return redirect(url_for('bins.index'))


@bins_bp.route('/<int:bin_id>/update-level', methods=['POST'])
@login_required
def update_level(bin_id):
    """AJAX endpoint to simulate an IoT sensor updating the fill level."""
    bin_obj = Bin.query.get_or_404(bin_id)
    new_level = request.json.get('fill_level')

    if new_level is None or not (0 <= float(new_level) <= 100):
        return jsonify({'error': 'Invalid fill level'}), 400

    bin_obj.fill_level = float(new_level)
    bin_obj.update_status()
    db.session.add(BinFillHistory(bin_id=bin_obj.id, fill_level=bin_obj.fill_level))
    _check_and_create_alert(bin_obj)
    db.session.commit()

    return jsonify({'success': True, 'bin': bin_obj.to_dict()})


@bins_bp.route('/<int:bin_id>/mark-collected', methods=['POST'])
@login_required
def mark_collected(bin_id):
    """Reset a bin to 0% after collection."""
    bin_obj = Bin.query.get_or_404(bin_id)
    bin_obj.fill_level = 0
    bin_obj.status = 'empty'
    bin_obj.last_collected_at = datetime.utcnow()
    db.session.add(BinFillHistory(bin_id=bin_obj.id, fill_level=0))

    # Resolve any open alerts for this bin
    Alert.query.filter_by(bin_id=bin_obj.id, is_resolved=False).update({
        'is_resolved': True, 'resolved_at': datetime.utcnow()
    })
    db.session.commit()

    log_activity(current_user.id, 'COLLECT_BIN', f'Bin {bin_obj.bin_code} emptied and reset')
    flash(f'Bin "{bin_obj.bin_code}" marked as collected and reset to 0%.', 'success')
    return redirect(request.referrer or url_for('bins.index'))
