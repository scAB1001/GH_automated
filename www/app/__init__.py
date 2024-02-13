from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_admin import Admin

# Create an instance of the Flask application
app = Flask(__name__)

# Load configuration settings from the DevelopmentConfig class in the config module
app.config.from_object('config.DevelopmentConfig')

# Initialize SQLAlchemy with the Flask app for database operations
db = SQLAlchemy(app)

# Initialize Migrate with the Flask app and SQLAlchemy db for database migrations
migrate = Migrate(app, db, render_as_batch=True)

# Initialize Admin with the Flask app for administrative interfaces
admin = Admin(app, template_mode='bootstrap4')


# Import views and models after app initialization to avoid circular imports
from app import views, models


# Register blueprints for different parts of the app
def register_blueprints(app):
    """
    Registers blueprints for different parts of the application.

    A blueprint is a way to organize a group of related views and other code. 
    Rather than registering views and other code directly with an application, 
    they are registered with a blueprint.

    Parameters:
    app: The Flask application instance.
    """
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')


# Call the function to register blueprints
register_blueprints(app)


# Configure the login manager for user authentication
def configure_login_manager(app):
    """
    Configures the login manager for user authentication.

    Initializes and configures the Flask-Login extension, which provides user session management.

    Parameters:
    app: The Flask application instance.
    """
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id: int):
        """
        Callback function for Flask-Login to load a user.

        Parameters:
        id: The user ID.

        Returns:
        The User object or None if not found.
        """
        from .models import User
        return db.session.get(User, id)


# Call the function to configure the login manager
configure_login_manager(app)
