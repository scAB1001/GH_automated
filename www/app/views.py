from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, session
from flask_login import login_required, logout_user, current_user
from .models import User, Car, UserInteraction
from app import app, db, admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.exc import IntegrityError
import json
from random import randint as r

# Adding models to the admin view for easy management
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Car, db.session))
admin.add_view(ModelView(UserInteraction, db.session))

# Constants for message categories
DANGER, SUCCESS = 'danger', 'success'
views = Blueprint('views', __name__)


def is_table_empty(model):
    """
    Checks if a given database table is empty.

    Parameters:
    model: The SQLAlchemy model class representing the database table.

    Returns:
    bool: True if the table is empty, False otherwise.
    """
    return db.session.query(model).count() == 0


def delete_user_interactions(user_id):
    """
    Deletes all interaction entries for a specific user.

    Parameters:
    user_id: ID of the user whose interaction entries are to be deleted.
    """
    try:
        to_delete = UserInteraction.query.filter_by(user_id=user_id)
        if to_delete.count() > 0:
            to_delete.delete()
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(
            f"An error occurred while deleting interactions for user ID {user_id}: {e}")


def pre_populate_tblCars():
    """
    Populates the Car table with a predefined list of cars.

    This function checks if the Car table is empty and, if so, adds a predefined list of cars to the database.
    """
    # random.randint -> r(1, 100)
    if is_table_empty(Car):
        try:
            # Car instances to be added
            cars_to_add = [
                Car(image='astonMartinSILagonda1', car_name='Aston Martin Lagonda Series 1', make='Aston Martin', model='Lagonda',
                    year=1974, body_type='4-door saloon', horsepower=280, monthly_payment=4611.96, mileage=18324, like_count=r(1, 100)),
                Car(image='astonMartinSIIILagonda3', car_name='Aston Martin Lagonda Series 3', make='Aston Martin', model='Lagonda',
                    year=1986, body_type='4-door saloon', horsepower=230, monthly_payment=7766.58, mileage=132084, like_count=r(1, 100)),
                Car(image='astonMartinSIVLagonda4', car_name='Aston Martin Lagonda Series 4', make='Aston Martin', model='Lagonda',
                    year=1987, body_type='4-door saloon', horsepower=240, monthly_payment=3633.98, mileage=123117, like_count=r(1, 100)),
                Car(image='ferrariTestarossa1', car_name='Ferrari Testarossa', make='Ferrari', model='Testarossa',
                    year=1984, body_type='2-door berlinetta', horsepower=385, monthly_payment=4185.91, mileage=146545, like_count=r(1, 100)),
                Car(image='ferrariF512TR3', car_name='Ferrari F512 TR', make='Ferrari', model='512 TR',
                    year=1991, body_type='2-door berlinetta', horsepower=422, monthly_payment=3245.32, mileage=198978, like_count=r(1, 100)),
                Car(image='ferrari308GTRainbow4', car_name='Ferrari 308 GT Bertone Rainbow', make='Ferrari', model='308 GT',
                    year=1976, body_type='2-door coupe', horsepower=255, monthly_payment=5585.91, mileage=89017, like_count=r(1, 100)),
                Car(image='countachLP400Lamborghini1', car_name='Lamborghini Countach LP400', make='Lamborghini', model='LP400',
                    year=1974, body_type='2-door coupe', horsepower=375, monthly_payment=8042.47, mileage=167228, like_count=r(1, 100)),
                Car(image='countachLP5000LamborghiniQuattrovalvole3', car_name='Lamborghini Countach Quattrovalvole', make='Lamborghini', 
                    model='LP5000', year=1985, body_type='2-door coupe', horsepower=455, monthly_payment=8930.27, mileage=103074, like_count=r(1, 100)),
                Car(image='countach25thAnniversaryLamborghini4', car_name='Lamborghini Countach 25th Anniversary', make='Lamborghini', 
                    model='25th Anniversary', year=1988, body_type='2-door coupe', horsepower=414, monthly_payment=6409.78, mileage=140320, like_count=r(1, 100))
            ]
            db.session.add_all(cars_to_add)
            db.session.commit()
            return jsonify({"status": "success", "message": "Cars added successfully"})
        except IntegrityError:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500


def prep_db():
    """
    Prepares the database by clearing tables and pre-populating them.

    This function first clears the session data, drops all database tables, 
        re-initialises all the database tables, pre-populates the Car table 
            and resets the login attempts counter.
    """
    db.session.remove()
    db.drop_all()
    db.create_all()
    session['login_attempts'] = 0
    pre_populate_tblCars()


@views.route('/toggle_count/<int:car_id>', methods=['POST'])
def toggle_count(car_id):
    """
    Route to handle like/dislike counts for cars.

    POST:
    Processes the user's like/dislike of a car and updates the like count in the database.

    Returns:
    JSON response: Contains the updated like count of the car.
    """
    car = db.session.get(Car, car_id)
    if not car:
        return jsonify({"error": "Car not found"}), 404

    liked = request.json.get('liked')

    # Check if liked is not a boolean
    if liked not in [True, False]:
        return jsonify({"error": "Invalid liked value"}), 400

    car.like_count += 1 if liked else -1
    
    db.session.commit()

    return jsonify(like_count=car.like_count)


@app.route('/react', methods=['POST'])
@login_required
def react():
    """
    Route to handle user swipe reactions to cars (like or dislike).

    POST:
    Processes the user's swipe reaction to a car and records it in the database.

    Returns:
    JSON response: Contains the status of the reaction, either success or error.
    """
    carID = request.json.get('carID')
    status = request.json.get('swiped_right')
    if not carID and not status:
        return jsonify({"status": "Invalid car ID and swiped_right provided"}), 400

    if not carID:
        return jsonify({"status": "Invalid car ID provided"}), 400 

    if status not in [True, False]:
        return jsonify({"status": "Invalid swiped_right provided"}), 400

    new_interaction = UserInteraction(
        user_id=current_user.id,
        car_id=carID,
        swiped_right=status
    )
    db.session.add(new_interaction)

    try:
        db.session.commit()
        return jsonify({"status": "success", "carID": carID, "swiped_right": status})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"status": "Unable to commit"}), 500


@app.route('/cards-depleted', methods=['POST'])
def cards_depleted():
    """
    Route to notify when all car cards have been swiped through.

    POST:
    Receives a signal indicating that all cards have been swiped.

    Returns:
    JSON response: Confirmation message indicating no more cards are available.
    """
    data = request.get_json()

    if data and data.get('isEmpty'):
        return jsonify({"message": "No more cards available"})
    
    elif data and not data.get('isEmpty'): #
        return jsonify({"message": "Cards still available"})
    
    return jsonify({"error": "Invalid request"}), 400


@views.route('/')
def home():
    """
    Home route.

    GET:
    Renders the homepage of the application.

    Returns:
    Rendered HTML: The homepage with a personalized greeting if the user is authenticated.
    """
    # prep_db()
    
    first_name = 'Guest'  # Default guest name
    if current_user.is_authenticated:
        first_name = current_user.first_name  # Personalized greeting for logged-in user

    return render_template('/site/home.html', title='Home', first_name=first_name, user=current_user)


@views.route('/explore')
@login_required
def explore():
    """
    Route to display the explore page with cars that the user has not yet interacted with.

    GET:
    Fetches cars that the current user hasn't liked or disliked yet and renders them on the explore page.

    Returns:
    Rendered HTML: The explore page with a list of cars for the user to interact with.
    """
    # Retrieve IDs of cars the user has interacted with
    interacted_car_ids = UserInteraction.query.with_entities(
        UserInteraction.car_id
    ).filter_by(user_id=current_user.id).all()

    # Convert list of tuples to a list of IDs
    interacted_car_ids = [car_id for (car_id,) in interacted_car_ids]

    # Fetch cars not yet interacted with by the user
    cars_to_swipe = Car.query.filter(Car.id.notin_(interacted_car_ids)).all()
    cars_remaining = [car.card_info() for car in cars_to_swipe]

    cars_remain = bool(cars_remaining)

    return render_template('/site/explore.html', title='Explore',
                           user=current_user, cars_remain=cars_remain, cars=cars_remaining)


@views.route('/saved')
@login_required
def saved():
    """
    Route to display the saved cars by the current user.

    GET:
    Fetches all cars that the current user has liked and renders them on the saved page.

    Returns:
    Rendered HTML: The saved page with a list of liked cars.
    """
    # Fetch liked interactions for the current user
    liked_interactions = UserInteraction.query.filter_by(
        user_id=current_user.id, swiped_right=True
    ).all()

    # Compile details of liked cars
    liked_cars = [db.session.get(Car, interaction.car_id).grid_view(
    ) for interaction in liked_interactions if db.session.get(Car, interaction.car_id)]
    
    liked_exist = bool(liked_cars)

    # Pass in like_count of each car
    for car in liked_cars:
        car['like_count'] = db.session.get(Car, car['carID']).like_count

    return render_template('/site/saved.html', title='Saved',
                           liked_exist=liked_exist, liked_cars=liked_cars, user=current_user)


@views.route('/saved/single-view/<int:carID>')
@login_required
def single_view(carID):
    """
    Route to display detailed view of a single car.

    GET:
    Fetches full details of a specific car based on its ID and renders them on the single view page.

    Parameters:
    carID (int): The ID of the car to be viewed.

    Returns:
    Rendered HTML: The single view page for the selected car.
    """
    # Fetch full details of the specified car
    car = db.session.get(Car, carID).full_details()

    return render_template('/site/single_view.html', title='Single View', user=current_user, car=car)


@views.route('/settings')
@login_required
def settings():
    """
    Route to display the user's settings page.

    GET:
    Renders the settings page for the current user.

    Returns:
    Rendered HTML: The settings page for the user.
    """
    return render_template('/site/settings.html', title='Settings', user=current_user)


@views.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """
    Route to handle account deletion requests.

    POST:
    Deletes the account of the currently authenticated user along with their interactions.

    Returns:
    Redirection to the login page after successful deletion, or an error message if the user is not authenticated.
    """
    if current_user.is_authenticated:
        # Fetch current user from the database
        user = db.session.get(User, current_user.id)
        
        # Delete user interactions
        delete_user_interactions(current_user.id)
        if user:
            db.session.delete(user)  # Delete the user
            db.session.commit()
            flash('Your account has successfully been deleted.', category=SUCCESS)
        else:
            flash('User not found.', category=DANGER)
        logout_user()  # Logout the user
        session['login_attempts'] = 0  # Reset login attempts
        return redirect(url_for('auth.login'))
    else:
        flash('You must be logged in to perform this action.', category=DANGER)
        return redirect(url_for('auth.login'))


@app.errorhandler(404)
def not_found_error(error):
    """
    Error handler for 404 Not Found error.

    Parameters:
    error: The error object provided by Flask.

    Returns:
    Rendered HTML: Custom 404 error page.
    """
    db.session.rollback()  # Rollback in case of any pending database transactions
    return render_template('/error/404.html', title='Error: 404', user=current_user), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Error handler for 500 Internal Server Error.

    Parameters:
    error: The error object provided by Flask.

    Returns:
    Rendered HTML: Custom 500 error page.
    """
    db.session.rollback()  # Rollback in case of any pending database transactions
    return render_template('/error/500.html', title='Error: 500', user=current_user), 500

