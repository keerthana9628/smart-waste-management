from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import Alert, log_activity

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')


@alerts_bp.route('/')
@login_required
def index():
    """Show active alerts and resolved alert history."""
    status_filter = request.args.get('status', 'active')

    if status_filter == 'resolved':
        alerts = Alert.query.filter_by(is_resolved=True).order_by(Alert.resolved_at.desc()).all()
    else:
        alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.created_at.desc()).all()

    return render_template('alerts.html', alerts=alerts, status_filter=status_filter)


@alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve(alert_id):
    """Mark a single alert as resolved."""
    alert = Alert.query.get_or_404(alert_id)
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.session.commit()

    log_activity(current_user.id, 'RESOLVE_ALERT', f'Resolved alert #{alert.id} for bin #{alert.bin_id}')
    flash('Alert marked as resolved.', 'success')
    return redirect(url_for('alerts.index'))


@alerts_bp.route('/resolve-all', methods=['POST'])
@login_required
def resolve_all():
    """Mark all active alerts as resolved."""
    count = Alert.query.filter_by(is_resolved=False).update({
        'is_resolved': True, 'resolved_at': datetime.utcnow()
    })
    db.session.commit()
    log_activity(current_user.id, 'RESOLVE_ALL_ALERTS', f'Resolved {count} alert(s)')
    flash(f'{count} alert(s) marked as resolved.', 'success')
    return redirect(url_for('alerts.index'))
