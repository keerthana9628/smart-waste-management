from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config_by_name

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name='development'):
    """Application factory for the Smart Waste Management System."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Import models so they are registered with SQLAlchemy
    from app import models  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.bins import bins_bp
    from app.routes.alerts import alerts_bp
    from app.routes.collections import collections_bp
    from app.routes.reports import reports_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(bins_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(collections_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Context processor: make unresolved alert count available in all templates
    @app.context_processor
    def inject_alert_count():
        from flask_login import current_user
        if current_user.is_authenticated:
            count = models.Alert.query.filter_by(is_resolved=False).count()
            return {'unresolved_alert_count': count}
        return {'unresolved_alert_count': 0}

    # Error handlers
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    return app
