from datetime import date, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Bin, Alert, Collection, ActivityLog
from app.ml.predictor import get_priority_bins

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard with key metrics, charts and recent activity."""

    total_bins = Bin.query.count()
    active_bins = Bin.query.filter(Bin.status != 'full').count()
    full_bins = Bin.query.filter_by(status='full').count()

    pending_collections = Collection.query.filter_by(status='pending').count()
    today_collections = Collection.query.filter_by(scheduled_date=date.today()).count()

    active_alerts = Alert.query.filter_by(is_resolved=False).count()

    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()

    # Bin status breakdown for pie chart
    status_counts = {
        'empty': Bin.query.filter_by(status='empty').count(),
        'half': Bin.query.filter_by(status='half').count(),
        'full': full_bins,
    }

    # All bins for the fill-level bar chart
    bins = Bin.query.order_by(Bin.fill_level.desc()).all()

    # AI predictive insights - top priority bins
    priority_bins = get_priority_bins(limit=5)

    # Waste collected over the last 7 days (for trend chart)
    week_ago = date.today() - timedelta(days=6)
    weekly_collections = (
        Collection.query
        .filter(Collection.status == 'completed', Collection.scheduled_date >= week_ago)
        .all()
    )
    daily_totals = {(week_ago + timedelta(days=i)).isoformat(): 0 for i in range(7)}
    for c in weekly_collections:
        key = c.scheduled_date.isoformat()
        if key in daily_totals and c.waste_collected_kg:
            daily_totals[key] += float(c.waste_collected_kg)

    return render_template(
        'dashboard.html',
        total_bins=total_bins,
        active_bins=active_bins,
        full_bins=full_bins,
        pending_collections=pending_collections,
        today_collections=today_collections,
        active_alerts=active_alerts,
        recent_activities=recent_activities,
        status_counts=status_counts,
        bins=bins,
        priority_bins=priority_bins,
        daily_totals=daily_totals,
    )
