from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model, UserMixin):
    """Represents Admin and Collector accounts."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum('admin', 'collector', name='user_role'), nullable=False, default='collector')
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    is_active_flag = db.Column('is_active', db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    collections = db.relationship('Collection', backref='collector', lazy='dynamic',
                                   foreign_keys='Collection.collector_id')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Bin(db.Model):
    """Represents a smart dustbin and its current state."""
    __tablename__ = 'bins'

    id = db.Column(db.Integer, primary_key=True)
    bin_code = db.Column(db.String(20), unique=True, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    latitude = db.Column(db.Numeric(10, 6))
    longitude = db.Column(db.Numeric(10, 6))
    capacity_l = db.Column(db.Integer, nullable=False, default=100)
    fill_level = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    status = db.Column(db.Enum('empty', 'half', 'full', name='bin_status'), nullable=False, default='empty')
    waste_type = db.Column(db.String(50), default='general')
    last_collected_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    history = db.relationship('BinFillHistory', backref='bin', lazy='dynamic',
                               cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='bin', lazy='dynamic',
                              cascade='all, delete-orphan')
    collections = db.relationship('Collection', backref='bin', lazy='dynamic',
                                   cascade='all, delete-orphan')

    def update_status(self):
        """Recalculate status enum based on current fill_level."""
        fl = float(self.fill_level)
        if fl >= 80:
            self.status = 'full'
        elif fl >= 30:
            self.status = 'half'
        else:
            self.status = 'empty'

    def to_dict(self):
        return {
            'id': self.id,
            'bin_code': self.bin_code,
            'location': self.location,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'capacity_l': self.capacity_l,
            'fill_level': float(self.fill_level),
            'status': self.status,
            'waste_type': self.waste_type,
            'last_collected_at': self.last_collected_at.isoformat() if self.last_collected_at else None,
        }

    def __repr__(self):
        return f'<Bin {self.bin_code} ({self.fill_level}%)>'


class BinFillHistory(db.Model):
    """Time-series fill level readings - used to train ML prediction models."""
    __tablename__ = 'bin_fill_history'

    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('bins.id'), nullable=False)
    fill_level = db.Column(db.Numeric(5, 2), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<History bin={self.bin_id} {self.fill_level}% @ {self.recorded_at}>'


class Alert(db.Model):
    """Auto-generated alerts when bins cross the fill threshold."""
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('bins.id'), nullable=False)
    alert_type = db.Column(db.Enum('fill_warning', 'full', 'maintenance', name='alert_type'),
                            nullable=False, default='fill_warning')
    message = db.Column(db.String(255), nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Alert bin={self.bin_id} {self.alert_type}>'


class Collection(db.Model):
    """Waste collection schedule and history record."""
    __tablename__ = 'collections'

    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('bins.id'), nullable=False)
    collector_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.Time)
    status = db.Column(db.Enum('pending', 'in_progress', 'completed', 'missed', name='collection_status'),
                        nullable=False, default='pending')
    waste_collected_kg = db.Column(db.Numeric(6, 2))
    collected_at = db.Column(db.DateTime)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Collection bin={self.bin_id} on {self.scheduled_date} ({self.status})>'


class ActivityLog(db.Model):
    """Audit trail of important system actions."""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ActivityLog {self.action} @ {self.created_at}>'


def log_activity(user_id, action, details=None):
    """Helper to record an activity log entry."""
    entry = ActivityLog(user_id=user_id, action=action, details=details)
    db.session.add(entry)
    db.session.commit()
