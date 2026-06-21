"""
Database Seeding Script
-------------------------
Creates all tables and populates the database with realistic sample
data, including:
  - Admin and collector user accounts
  - 12 sample bins across a campus
  - ~5 days of fill-level history per bin (used to train the ML
    fill-rate predictor)
  - Alerts for bins above the threshold
  - Collection schedules (pending + completed history)
  - Sample activity logs

Run this AFTER creating the MySQL database (see database/schema.sql or
let this script call db.create_all() to create tables automatically).

Usage:
    python seed_db.py
"""

import random
from datetime import datetime, timedelta, date, time

from app import create_app, db
from app.models import User, Bin, BinFillHistory, Alert, Collection, ActivityLog

app = create_app('development')


# ----------------------------------------------------------------
# Sample bin definitions: (code, location, capacity, waste_type,
#                          current_fill_level, hourly_fill_rate)
# ----------------------------------------------------------------
BIN_DEFS = [
    ('BIN-001', 'Main Gate',           120, 'general',    92.0, 1.9),
    ('BIN-002', 'Library Block',       100, 'general',    45.0, 0.9),
    ('BIN-003', 'Canteen Area',        150, 'organic',    88.0, 2.4),
    ('BIN-004', 'AIML Department',     100, 'general',    22.0, 0.5),
    ('BIN-005', 'Hostel Block A',      200, 'general',    67.0, 1.3),
    ('BIN-006', 'Hostel Block B',      200, 'general',    81.0, 1.6),
    ('BIN-007', 'Sports Ground',       100, 'general',    15.0, 0.4),
    ('BIN-008', 'Admin Block',         100, 'general',    53.0, 1.0),
    ('BIN-009', 'Mechanical Workshop', 150, 'recyclable', 30.0, 0.6),
    ('BIN-010', 'Parking Area',        100, 'general',    76.0, 1.5),
    ('BIN-011', 'Auditorium',          150, 'general',    95.0, 2.0),
    ('BIN-012', 'Faculty Quarters',    100, 'general',    10.0, 0.3),
]


def seed():
    with app.app_context():
        print('Creating tables (if they do not already exist)...')
        db.create_all()

        if User.query.first():
            print('Database already contains data. Skipping seed to avoid duplicates.')
            print('To reseed from scratch, drop the database and recreate it first.')
            return

        # ------------------------------------------------------------
        # Users
        # ------------------------------------------------------------
        print('Creating users...')
        admin = User(username='admin', full_name='System Administrator',
                      role='admin', email='admin@ewit.edu', phone='9000000001')
        admin.set_password('password123')

        collector1 = User(username='collector1', full_name='Ravi Kumar',
                           role='collector', email='ravi@ewit.edu', phone='9000000002')
        collector1.set_password('password123')

        collector2 = User(username='collector2', full_name='Suresh Babu',
                           role='collector', email='suresh@ewit.edu', phone='9000000003')
        collector2.set_password('password123')

        collector3 = User(username='collector3', full_name='Lakshmi Narayan',
                           role='collector', email='lakshmi@ewit.edu', phone='9000000004')
        collector3.set_password('password123')

        db.session.add_all([admin, collector1, collector2, collector3])
        db.session.commit()
        collectors = [collector1, collector2, collector3]

        # ------------------------------------------------------------
        # Bins + fill history (for ML model training)
        # ------------------------------------------------------------
        print('Creating bins and fill-level history (this may take a moment)...')
        now = datetime.utcnow()
        history_days = 5
        readings_per_day = 6  # every 4 hours

        bins = []
        for code, location, capacity, waste_type, current_level, hourly_rate in BIN_DEFS:
            last_collected = now - timedelta(days=random.randint(1, 5))

            bin_obj = Bin(
                bin_code=code,
                location=location,
                capacity_l=capacity,
                fill_level=current_level,
                waste_type=waste_type,
                last_collected_at=last_collected,
                latitude=12.9352 + random.uniform(0, 0.005),
                longitude=77.5347 + random.uniform(0, 0.005),
            )
            bin_obj.update_status()
            db.session.add(bin_obj)
            db.session.flush()
            bins.append(bin_obj)

            # Generate history: work backwards from current_level using
            # the hourly_rate, clamped to >= 0, only after last_collected
            total_readings = history_days * readings_per_day
            for i in range(total_readings, -1, -1):
                ts = now - timedelta(hours=i * 4)
                if ts < last_collected:
                    continue
                hours_since_collection = (ts - last_collected).total_seconds() / 3600.0
                level = min(hourly_rate * hours_since_collection + random.uniform(-1.5, 1.5), 100)
                level = max(level, 0)
                db.session.add(BinFillHistory(bin_id=bin_obj.id, fill_level=round(level, 2),
                                               recorded_at=ts))

            # Ensure the final history point matches the bin's current level
            db.session.add(BinFillHistory(bin_id=bin_obj.id, fill_level=current_level, recorded_at=now))

        db.session.commit()

        # ------------------------------------------------------------
        # Alerts (auto-generated for bins above threshold)
        # ------------------------------------------------------------
        print('Creating alerts...')
        for bin_obj in bins:
            if float(bin_obj.fill_level) >= 80:
                alert_type = 'full' if float(bin_obj.fill_level) >= 95 else 'fill_warning'
                db.session.add(Alert(
                    bin_id=bin_obj.id,
                    alert_type=alert_type,
                    message=f'{bin_obj.bin_code} ({bin_obj.location}) has reached '
                            f'{bin_obj.fill_level}% capacity.',
                    created_at=now - timedelta(hours=random.randint(1, 12))
                ))
        db.session.commit()

        # ------------------------------------------------------------
        # Collections - pending tasks for urgent bins + completed history
        # ------------------------------------------------------------
        print('Creating collection schedules and history...')
        urgent_bins = [b for b in bins if float(b.fill_level) >= 80]
        for i, bin_obj in enumerate(urgent_bins):
            db.session.add(Collection(
                bin_id=bin_obj.id,
                collector_id=collectors[i % len(collectors)].id,
                scheduled_date=date.today(),
                scheduled_time=time(9, 0),
                status='pending',
                notes='Urgent - bin above 80% capacity'
            ))

        # Completed history over the last 7 days
        for day_offset in range(1, 8):
            for _ in range(random.randint(1, 3)):
                bin_obj = random.choice(bins)
                collector = random.choice(collectors)
                completed_date = date.today() - timedelta(days=day_offset)
                db.session.add(Collection(
                    bin_id=bin_obj.id,
                    collector_id=collector.id,
                    scheduled_date=completed_date,
                    scheduled_time=time(random.choice([9, 10, 11, 14]), 0),
                    status='completed',
                    waste_collected_kg=round(random.uniform(5, 40), 1),
                    collected_at=datetime.combine(completed_date, time(10, 0)),
                    notes='Routine collection'
                ))

        db.session.commit()

        # ------------------------------------------------------------
        # Activity logs
        # ------------------------------------------------------------
        print('Creating activity logs...')
        db.session.add_all([
            ActivityLog(user_id=admin.id, action='LOGIN', details='Admin logged in', created_at=now - timedelta(hours=6)),
            ActivityLog(user_id=admin.id, action='ADD_BIN', details='Added new bin BIN-012 at Faculty Quarters', created_at=now - timedelta(hours=5)),
            ActivityLog(user_id=admin.id, action='CREATE_SCHEDULE', details='Created collection schedule for BIN-001', created_at=now - timedelta(hours=3)),
            ActivityLog(user_id=collector1.id, action='UPDATE_COLLECTION', details='Marked BIN-002 collection as completed', created_at=now - timedelta(hours=2)),
            ActivityLog(user_id=admin.id, action='RESOLVE_ALERT', details='Resolved alert for BIN-010', created_at=now - timedelta(hours=1)),
        ])
        db.session.commit()

        print('\nSeed data created successfully!')
        print('=' * 50)
        print('Login credentials (all use password: password123)')
        print('  Admin:      admin')
        print('  Collector:  collector1 / collector2 / collector3')
        print('=' * 50)


if __name__ == '__main__':
    seed()
