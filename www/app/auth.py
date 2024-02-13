from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, login_required, logout_user, current_user
from .auth_service import authenticate_and_login, register_and_login
from .forms import LoginForm, RegistrationForm

# Blueprint setup for authentication routes
auth = Blueprint('auth', __name__)

# Constants for flash message categories and content
SUCCESS = 'success'
ERROR = 'error'
LOGOUT_SUCCESS = 'Signed out successfully!'
INVALID_CREDENTIALS = 'Incorrect email or password, try again.'
MAX_LOGIN_ATTEMPTS_REACHED = 'Maximum sign-in attempts reached.'

# Maximum allowed login attempts
MAX_LOGIN_ATTEMPTS = 3


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Route to handle user login.

    GET: Renders the login form.
    POST: Processes the login form and authenticates the user.

    Returns:
        On successful login: A redirection to the homepage.
        On login failure: The login page with an error message.
        On exceeding maximum login attempts: Redirect to the signup page.
    """
    form = LoginForm()

    if session.get('login_attempts', 0) >= MAX_LOGIN_ATTEMPTS:
        flash(MAX_LOGIN_ATTEMPTS_REACHED, ERROR)
        return redirect(url_for('auth.signup'))

    if form.validate_on_submit():
        if authenticate_and_login(form.email.data, form.password.data):
            # Reset login attempts on successful login
            session['login_attempts'] = 0
            return redirect(url_for('views.home'))
        else:
            session['login_attempts'] = session.get('login_attempts', 0) + 1
            flash(INVALID_CREDENTIALS, ERROR)

    return render_template("/admin/login.html", form=form, user=current_user, title='Login')


@auth.route('/logout')
@login_required
def logout():
    """
    Route to handle user logout.

    The user is logged out and redirected to the home page.
    Login attempts are reset.

    Returns:
        Redirection to the home page.
    """
    logout_user()
    session.pop('login_attempts', None)  # Clear login attempts
    flash(LOGOUT_SUCCESS, SUCCESS)
    return redirect(url_for('views.home'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Route to handle user registration.

    GET: Renders the registration form.
    POST: Processes the registration form and registers the user.

    If the user is already logged in, they are logged out before proceeding.

    Returns:
        On successful registration: A redirection to the homepage.
        On registration failure: The signup page with an error message.
    """
    if current_user.is_authenticated:
        logout_user()  # Logout current user if logged in

    form = RegistrationForm()
    if form.validate_on_submit():
        if register_and_login(form.email.data, form.first_name.data, form.password.data, form.confirm_password.data):
            # Reset login attempts on successful sign-up
            session.pop('login_attempts', None)
            return redirect(url_for('views.home'))
        # Error messages are handled within the register_and_login function

    return render_template("/admin/signup.html", form=form, user=current_user, title='Signup')
