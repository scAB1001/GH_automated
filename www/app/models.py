from app import db
from sqlalchemy.sql import func
from flask_login import UserMixin

# Constant fo default datetime
DT = func.now()


class BaseModel(db.Model):
    """
    Base class for all SQLAlchemy models in the application.

    Attributes:
    - id (int): Primary key for the model.
    - created_at (datetime): Timestamp of when the record was created, set by default to the current time.
    - updated_at (datetime): Timestamp of the last update to the record, updated automatically to the current time on record update.

    This class is abstract and is intended to be inherited by other models.
    """
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=DT)
    updated_at = db.Column(db.DateTime(timezone=True), default=DT, onupdate=DT)


class User(BaseModel, UserMixin):
    """
    User model representing a user in the system.

    Inherits from BaseModel and adds specific fields and relationships for a user.

    Attributes:
    - email (String): The user's email address, unique across the system.
    - password (String): The user's hashed password.
    - first_name (String): The user's first name.
    - interactions (relationship): A list of interactions (likes/dislikes) associated with the user.

    The __repr__ method provides a simple representation of the user.
    """
    __tablename__ = 'user'

    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    interactions = db.relationship('UserInteraction', backref='user', lazy=True)


    def __repr__(self):
        return f"User {self.id}: {self.first_name}, {self.email}"


class Car(BaseModel):
    """
    Car model representing a car in the system.

    Inherits from BaseModel and adds specific fields for a car.

    Attributes:
    - image (String): URL or path to the car's image.
    - car_name (String): The name of the car.
    - make (String): The make of the car.
    - model (String): The model of the car.
    - year (Integer): The manufacturing year of the car.
    - body_type (String): The body type of the car.
    - horsepower (Integer): The horsepower of the car.
    - monthly_payment (Float): The monthly payment amount for the car.
    - mileage (Integer): The mileage of the car.
    - like_count (Integer): The number of likes the car has received from other users.
    - interactions (relationship): A list of interactions (likes/dislikes) associated with the car.

    The __repr__ method provides a simple representation of the car.
    """
    __tablename__ = 'cars'

    image = db.Column(db.String(255), unique=True, nullable=False)
    car_name = db.Column(db.String(255), unique=True, nullable=False)
    make = db.Column(db.String(255), nullable=False)
    model = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    body_type = db.Column(db.String(255), nullable=False)
    horsepower = db.Column(db.Integer, nullable=False)
    monthly_payment = db.Column(db.Float, nullable=False)
    mileage = db.Column(db.Integer, nullable=False)
    like_count = db.Column(db.Integer, default=2, nullable=False)
    interactions = db.relationship('UserInteraction', backref='car', lazy=True)


    def __repr__(self):
        return f"Car {self.id}: {self.make}, {self.model}, {self.year}"

    def grid_view(self):
        """
        Prepares and returns a simplified dictionary of the car's details for grid display.

        Returns:
        Dictionary: A simplified view of the car's details, including ID, image URL, and name.
        """
        return {
            'carID': int(str(self.id)),
            'imageUrl': f'{self.image}',
            'carName': f'{self.car_name}'
        }

    def card_info(self):
        """
        Prepares and returns detailed information about the car for card display.

        The information includes the car's ID, image URL, name, and additional details formatted for display.

        Returns:
        Dictionary: A detailed view of the car's information for card display.
        """
        width = 20
        return {
            'carID': int(str(self.id)),
            'imageUrl': f'{self.image}',
            'carName': f'{self.car_name}'.center(width),
            'details': f'Price: £{self.monthly_payment}pm'.ljust(width) +
                       f' Body: {self.body_type}'.rjust(width) + '\n' +
                       f'Horsepower: {self.horsepower}bhp'.ljust(width) +
                       f' Make: {self.make}'.rjust(width)
        }

    def full_details(self):
        """
        Prepares and returns a comprehensive dictionary of the car's details for a detailed view.

        This method is used for displaying full details in sections like 'Saved (single_view)'.

        Returns:
        Dictionary: A comprehensive view of the car's information, including all relevant details.
        """
        return {
            'imageUrl': f'{self.image}',
            'carName': f'{self.car_name}',
            'make': f'{self.make}',
            'model': f'{self.model}',
            'year': f'{self.year}',
            'body_type': f'{self.body_type}',
            'horsepower': f'{self.horsepower}',
            'monthly_payment': f'{self.monthly_payment}',
            'mileage': f'{self.mileage}'
        }


class UserInteraction(BaseModel):
    """
    UserInteraction model representing a user's interaction (like/dislike) with a car.

    Inherits from BaseModel and adds specific fields for the interaction.

    Attributes:
    - user_id (Integer): Foreign key linking to the User model.
    - car_id (Integer): Foreign key linking to the Car model.
    - swiped_right (Boolean): Represents if the user liked (True) or disliked (False) the car.
    - timestamp (DateTime): The timestamp when the interaction occurred.

    The __repr__ method provides a simple representation of the user interaction.
    """
    __tablename__ = 'user_interactions'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    swiped_right = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=DT)

    def __repr__(self):
        return f"UserInteraction {self.id}: User {self.user_id}, Car {self.car_id}, Liked: {self.swiped_right}"
