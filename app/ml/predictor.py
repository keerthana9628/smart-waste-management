"""
ML Module: Bin Fill-Level Predictor
------------------------------------
Uses simple linear regression (scikit-learn) on each bin's historical
fill-level readings (bin_fill_history) to estimate:
  - the average fill rate (% per hour)
  - the predicted date/time the bin will cross the alert threshold (80%)
  - the predicted date/time the bin will become completely full (100%)

If a bin has fewer than 2 history points, a sensible default rate is
assumed so the dashboard always has something useful to display.
"""

from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression

from app import db
from app.models import Bin, BinFillHistory

# Fallback fill rate (percent per hour) used when there isn't enough
# history to train a model for a bin.
DEFAULT_FILL_RATE_PER_HOUR = 1.5
ALERT_THRESHOLD = 80.0
FULL_THRESHOLD = 100.0


def _get_history_since_last_collection(bin_obj):
    """Return (timestamps, fill_levels) for readings recorded after the
    bin's last collection (or all history if never collected)."""
    query = BinFillHistory.query.filter_by(bin_id=bin_obj.id)
    if bin_obj.last_collected_at:
        query = query.filter(BinFillHistory.recorded_at >= bin_obj.last_collected_at)
    history = query.order_by(BinFillHistory.recorded_at.asc()).all()
    return history


def predict_bin(bin_obj):
    """Predict fill-rate and time-to-threshold for a single bin.

    Returns a dict with prediction details. Falls back to a default
    growth rate when there isn't enough historical data to fit a model.
    """
    history = _get_history_since_last_collection(bin_obj)
    current_level = float(bin_obj.fill_level)
    now = datetime.utcnow()

    rate_per_hour = DEFAULT_FILL_RATE_PER_HOUR
    model_used = 'default_rate'

    if len(history) >= 2:
        # Convert timestamps to hours elapsed since the first reading
        t0 = history[0].recorded_at
        X = np.array([(h.recorded_at - t0).total_seconds() / 3600.0 for h in history]).reshape(-1, 1)
        y = np.array([float(h.fill_level) for h in history])

        model = LinearRegression()
        model.fit(X, y)
        slope = model.coef_[0]

        # Only trust the model if the trend is increasing (bins fill up,
        # they don't spontaneously empty without a collection event)
        if slope > 0.01:
            rate_per_hour = slope
            model_used = 'linear_regression'

    # Hours remaining until thresholds are reached
    hours_to_alert = max((ALERT_THRESHOLD - current_level) / rate_per_hour, 0) \
        if current_level < ALERT_THRESHOLD else 0
    hours_to_full = max((FULL_THRESHOLD - current_level) / rate_per_hour, 0) \
        if current_level < FULL_THRESHOLD else 0

    return {
        'bin_id': bin_obj.id,
        'bin_code': bin_obj.bin_code,
        'location': bin_obj.location,
        'current_fill_level': current_level,
        'fill_rate_per_hour': round(rate_per_hour, 3),
        'model_used': model_used,
        'data_points': len(history),
        'predicted_alert_time': (now + timedelta(hours=hours_to_alert)).isoformat() if hours_to_alert else None,
        'predicted_full_time': (now + timedelta(hours=hours_to_full)).isoformat() if hours_to_full else None,
        'hours_to_alert': round(hours_to_alert, 1),
        'hours_to_full': round(hours_to_full, 1),
    }


def predict_all_bins():
    """Return predictions for every bin, sorted by urgency (soonest to
    reach the alert threshold first)."""
    bins = Bin.query.all()
    predictions = [predict_bin(b) for b in bins]
    predictions.sort(key=lambda p: p['hours_to_alert'])
    return predictions


def get_priority_bins(limit=5):
    """Return the `limit` bins predicted to require attention soonest."""
    predictions = predict_all_bins()
    # Only show bins not already full / already over threshold first,
    # then the rest ordered by urgency.
    return predictions[:limit]
