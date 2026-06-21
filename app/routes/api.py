from datetime import date, timedelta
from flask import Blueprint, jsonify
from flask_login import login_required

from app.models import Bin, BinFillHistory, Collection
from app.ml.predictor import predict_all_bins
from app.ml.scheduler_ai import generate_schedule

api_bp = Blueprint('api', __name__)


@api_bp.route('/bins')
@login_required
def bins_list():
    """Return all bins as JSON (used for map / table refresh)."""
    bins = Bin.query.all()
    return jsonify([b.to_dict() for b in bins])


@api_bp.route('/bins/<int:bin_id>/history')
@login_required
def bin_history(bin_id):
    """Return fill-level history for a single bin (for trend chart)."""
    history = (
        BinFillHistory.query
        .filter_by(bin_id=bin_id)
        .order_by(BinFillHistory.recorded_at.asc())
        .all()
    )
    return jsonify([
        {'recorded_at': h.recorded_at.isoformat(), 'fill_level': float(h.fill_level)}
        for h in history
    ])


@api_bp.route('/predictions')
@login_required
def predictions():
    """Return ML fill-level predictions for all bins."""
    return jsonify(predict_all_bins())


@api_bp.route('/ai-schedule')
@login_required
def ai_schedule():
    """Return the AI-optimized collection schedule preview."""
    return jsonify(generate_schedule())


@api_bp.route('/waste-trend')
@login_required
def waste_trend():
    """Return daily waste-collection totals for the last 30 days."""
    start = date.today() - timedelta(days=29)
    collections = (
        Collection.query
        .filter(Collection.status == 'completed', Collection.scheduled_date >= start)
        .all()
    )

    daily_totals = {(start + timedelta(days=i)).isoformat(): 0 for i in range(30)}
    for c in collections:
        key = c.scheduled_date.isoformat()
        if key in daily_totals and c.waste_collected_kg:
            daily_totals[key] += float(c.waste_collected_kg)

    return jsonify({
        'labels': list(daily_totals.keys()),
        'values': list(daily_totals.values())
    })


@api_bp.route('/bin-status-summary')
@login_required
def bin_status_summary():
    """Return counts of bins by status (for pie chart)."""
    return jsonify({
        'empty': Bin.query.filter_by(status='empty').count(),
        'half': Bin.query.filter_by(status='half').count(),
        'full': Bin.query.filter_by(status='full').count(),
    })
