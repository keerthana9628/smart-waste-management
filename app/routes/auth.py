from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, log_activity

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Display login form and authenticate the user."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active_flag:
                flash('Your account has been deactivated. Contact the administrator.', 'danger')
                return render_template('login.html')

            login_user(user, remember=remember)
            log_activity(user.id, 'LOGIN', f'{user.role.capitalize()} "{user.username}" logged in')
            flash(f'Welcome back, {user.full_name}!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))

        flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Log the current user out."""
    log_activity(current_user.id, 'LOGOUT', f'User "{current_user.username}" logged out')
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
