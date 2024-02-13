import os

# Determine the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """
    Base configuration class with common settings.

    Attributes:
    - SECRET_KEY (str): The secret key used by Flask for various cryptographic functions.
    - SQLALCHEMY_DATABASE_URI (str): Database connection string.
    - SQLALCHEMY_TRACK_MODIFICATIONS (bool): Flag to track modifications of objects and emit signals.
    - WTF_CSRF_ENABLED (bool): Flag to enable/disable CSRF protection in forms.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-fallback-secret-key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    """
    Development-specific configuration class.

    Inherits from the base Config class and overrides or extends it with development-specific settings.

    Attributes:
    - PORT (int): The port on which the Flask application will run.
    - DEBUG (bool): Enables/Disables debug mode in Flask.
    """
    PORT = 80
    DEBUG = True
    # Other development-specific settings can be added here


class ProductionConfig(Config):
    """
    Production-specific configuration class.

    Inherits from the base Config class and overrides or extends it with production-specific settings.

    Attributes:
    - PORT (int): The port on which the Flask application will run.
    - DEBUG (bool): Enables/Disables debug mode in Flask.
    """
    PORT = 131
    DEBUG = False
    # Other production-specific settings can be added here
