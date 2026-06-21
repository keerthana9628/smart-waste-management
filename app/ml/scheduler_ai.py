"""
ML Module: AI-Optimized Collection Scheduler
---------------------------------------------
Generates a suggested collection schedule by:
  1. Scoring every bin's "urgency" using its current fill level and its
     predicted time-to-full (from predictor.py).
  2. Selecting the bins that need collection soon (urgency above a
     configurable cut-off, or already over the alert threshold).
  3. Distributing those bins evenly across available collectors
     (load-balancing), assigning the most urgent bins first.
  4. Spreading collections across the next N days so no collector is
     overloaded on a single day.
"""

from datetime import date, timedelta
from app.models import User
from app.ml.predictor import predict_all_bins, ALERT_THRESHOLD


def _urgency_score(prediction):
    """Higher score = more urgent. Combines current fill level with how
    soon the bin is predicted to cross the alert threshold."""
    current = prediction['current_fill_level']
    hours_to_alert = prediction['hours_to_alert']

    # Already over threshold -> maximum urgency, ranked by current level
    if current >= ALERT_THRESHOLD:
        return 1000 + current

    # Otherwise, urgency increases the sooner the bin will reach 80%
    # (fewer hours = higher score). Cap to avoid division issues.
    return 1 / (hours_to_alert + 1)


def generate_schedule(days_ahead=3, max_per_collector_per_day=4):
    """Generate a suggested collection schedule.

    Returns a list of dicts:
        { bin_id, bin_code, location, fill_level, urgency,
          collector_id, collector_name, scheduled_date }
    """
    predictions = predict_all_bins()

    # Rank bins by urgency (descending)
    ranked = sorted(predictions, key=_urgency_score, reverse=True)

    # Only include bins that are at/above the alert threshold OR
    # predicted to reach it within the planning window
    window_hours = days_ahead * 24
    candidates = [
        p for p in ranked
        if p['current_fill_level'] >= ALERT_THRESHOLD or p['hours_to_alert'] <= window_hours
    ]

    collectors = User.query.filter_by(role='collector', is_active_flag=True).all()
    if not collectors:
        return []

    schedule = []
    # Track how many bins each collector has been assigned per day
    load = {c.id: {d: 0 for d in range(days_ahead)} for c in collectors}

    for prediction in candidates:
        assigned = False
        for day_offset in range(days_ahead):
            # Find the collector with the lowest load on this day
            collector = min(collectors, key=lambda c: load[c.id][day_offset])
            if load[collector.id][day_offset] < max_per_collector_per_day:
                load[collector.id][day_offset] += 1
                schedule.append({
                    'bin_id': prediction['bin_id'],
                    'bin_code': prediction['bin_code'],
                    'location': prediction['location'],
                    'fill_level': prediction['current_fill_level'],
                    'urgency_score': round(_urgency_score(prediction), 3),
                    'collector_id': collector.id,
                    'collector_name': collector.full_name,
                    'scheduled_date': (date.today() + timedelta(days=day_offset)).isoformat(),
                })
                assigned = True
                break
        if not assigned:
            # Everyone is at capacity for the whole window - schedule for
            # the last day with whoever has the least load anyway.
            collector = min(collectors, key=lambda c: load[c.id][days_ahead - 1])
            schedule.append({
                'bin_id': prediction['bin_id'],
                'bin_code': prediction['bin_code'],
                'location': prediction['location'],
                'fill_level': prediction['current_fill_level'],
                'urgency_score': round(_urgency_score(prediction), 3),
                'collector_id': collector.id,
                'collector_name': collector.full_name,
                'scheduled_date': (date.today() + timedelta(days=days_ahead - 1)).isoformat(),
            })

    return schedule
