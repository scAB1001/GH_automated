from config import SQLALCHEMY_DATABASE_URI
from app import db
import os.path

# This script is used to initialize the database for the application.

if __name__ == '__main__':
    """
    Main execution block.

    This script checks if the database file already exists before attempting to create it. 
    It ensures that running the script multiple times does not lead to unintended consequences.
    """
    # Define the path for the database file
    db_file = os.path.join(os.path.dirname(__file__), 'app.db')

    # Check if the database file already exists
    if not os.path.exists(db_file):
        # If the database file does not exist, create a new database
        with app.app_context():
            db.create_all()  # Create all tables defined in the SQLAlchemy models
            print("Database created.")  # Print confirmation message
    else:
        # If the database file exists, print a message stating so
        print("Database already exists.")
