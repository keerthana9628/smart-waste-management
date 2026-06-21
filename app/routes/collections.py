from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Collection, Bin, User, BinFillHistory, Alert, log_activity
from app.utils.decorators import admin_required
from app.ml.scheduler_ai import generate_schedule

collections_bp = Blueprint('collections', __name__, url_prefix='/collections')


@collections_bp.route('/')
@login_required
def index():
    """List collection schedules. Collectors see only their own tasks."""
    status_filter = request.args.get('status', '')

    query = Collection.query
    if current_user.role == 'collector':
        query = query.filter_by(collector_id=current_user.id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    collections = query.order_by(Collection.scheduled_date.desc(), Collection.id.desc()).all()
    bins = Bin.query.order_by(Bin.bin_code).all()
    collectors = User.query.filter_by(role='collector', is_active_flag=True).all()

    return render_template(
        'collections.html',
        collections=collections,
        bins=bins,
        collectors=collectors,
        status_filter=status_filter
    )


@collections_bp.route('/create', methods=['POST'])
@login_required
@admin_required
def create():
    """Create a new collection schedule (manual)."""
    bin_id = request.form.get('bin_id')
    collector_id = request.form.get('collector_id') or None
    scheduled_date = request.form.get('scheduled_date')
    scheduled_time = request.form.get('scheduled_time') or None
    notes = request.form.get('notes', '').strip()

    new_collection = Collection(
        bin_id=bin_id,
        collector_id=collector_id,
        scheduled_date=datetime.strptime(scheduled_date, '%Y-%m-%d').date(),
        scheduled_time=datetime.strptime(scheduled_time, '%H:%M').time() if scheduled_time else None,
        notes=notes or None,
        status='pending'
    )
    db.session.add(new_collection)
    db.session.commit()

    bin_obj = Bin.query.get(bin_id)
    log_activity(current_user.id, 'CREATE_SCHEDULE',
                  f'Created collection schedule for {bin_obj.bin_code} on {scheduled_date}')
    flash('Collection schedule created successfully.', 'success')
    return redirect(url_for('collections.index'))


@collections_bp.route('/<int:collection_id>/update-status', methods=['POST'])
@login_required
def update_status(collection_id):
    """Update the status of a collection task (collector or admin)."""
    collection = Collection.query.get_or_404(collection_id)

    # Collectors may only update their own tasks
    if current_user.role == 'collector' and collection.collector_id != current_user.id:
        flash('You can only update tasks assigned to you.', 'danger')
        return redirect(url_for('collections.index'))

    new_status = request.form.get('status')
    waste_kg = request.form.get('waste_collected_kg')

    collection.status = new_status
    if new_status == 'completed':
        collection.collected_at = datetime.utcnow()
        if waste_kg:
            collection.waste_collected_kg = float(waste_kg)

        # Reset the bin's fill level since it has been emptied
        bin_obj = collection.bin
        bin_obj.fill_level = 0
        bin_obj.status = 'empty'
        bin_obj.last_collected_at = datetime.utcnow()
        db.session.add(BinFillHistory(bin_id=bin_obj.id, fill_level=0))

        # Resolve any open alerts for this bin
        Alert.query.filter_by(bin_id=bin_obj.id, is_resolved=False).update({
            'is_resolved': True, 'resolved_at': datetime.utcnow()
        })

    db.session.commit()
    log_activity(current_user.id, 'UPDATE_COLLECTION',
                  f'Collection #{collection.id} for bin {collection.bin.bin_code} marked as {new_status}')
    flash('Collection status updated.', 'success')
    return redirect(url_for('collections.index'))


@collections_bp.route('/<int:collection_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(collection_id):
    """Delete a collection schedule entry."""
    collection = Collection.query.get_or_404(collection_id)
    db.session.delete(collection)
    db.session.commit()
    flash('Collection schedule deleted.', 'success')
    return redirect(url_for('collections.index'))


@collections_bp.route('/ai-schedule', methods=['GET'])
@login_required
@admin_required
def ai_schedule():
    """Preview an AI-generated optimized collection schedule."""
    suggestions = generate_schedule()
    return render_template('ai_schedule.html', suggestions=suggestions)


@collections_bp.route('/ai-schedule/apply', methods=['POST'])
@login_required
@admin_required
def apply_ai_schedule():
    """Persist the AI-generated schedule as real Collection records."""
    suggestions = generate_schedule()
    created = 0

    for s in suggestions:
        # Avoid duplicate pending schedules for the same bin/date
        existing = Collection.query.filter_by(
            bin_id=s['bin_id'],
            scheduled_date=datetime.strptime(s['scheduled_date'], '%Y-%m-%d').date(),
            status='pending'
        ).first()
        if existing:
            continue

        db.session.add(Collection(
            bin_id=s['bin_id'],
            collector_id=s['collector_id'],
            scheduled_date=datetime.strptime(s['scheduled_date'], '%Y-%m-%d').date(),
            status='pending',
            notes=f"AI-generated (urgency score: {s['urgency_score']})"
        ))
        created += 1

    db.session.commit()
    log_activity(current_user.id, 'APPLY_AI_SCHEDULE', f'Applied AI schedule - {created} task(s) created')
    flash(f'AI schedule applied: {created} new collection task(s) created.', 'success')
    return redirect(url_for('collections.index'))
