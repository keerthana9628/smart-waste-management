import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration for the Smart Waste Management System."""

    # Secret key used for session signing / CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # ----------------------------------------------------------------
    # Database configuration (MySQL via PyMySQL driver)
    # Format: mysql+pymysql://<user>:<password>@<host>/<db_name>
    # ----------------------------------------------------------------
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'smart_waste_db')

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Alert threshold (percentage) - bins above this trigger alerts
    FILL_ALERT_THRESHOLD = 80.0

    # Pagination
    ITEMS_PER_PAGE = 10


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
