import os, unittest, json, re
from unittest.mock import patch
from flask import Flask, session
from app import app, db
from flask_login import login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from app.forms import LoginForm, RegistrationForm
from app.models import User, Car, UserInteraction
from app.auth import login, logout, signup, MAX_LOGIN_ATTEMPTS
from app.auth_service import generate_hash, validate_password, valid_inputs, authenticate_and_login, create_user, register_and_login
from app.views import home, explore, saved, single_view, settings, delete_account

basedir = os.path.abspath(os.path.dirname(__file__))


class BasicTestCase(unittest.TestCase):
    # Boilerplate code for setting up/tearing down the test env
    def setUp(self):
        """
        Creates a new database for the unit test to use

        :return: None
        """
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
            os.path.join(basedir, 'app.db')

        self.app = app.test_client()

        with app.app_context():
            db.create_all()

            if os.path.exists(os.path.join(basedir, 'app.db')):
                self._create_test_data()
                print("\tTest environment intialised.")


    def _create_test_data(self):
        """
        Creates test data for the unit test to use

        :return: None
        """
        # Create users
        user1 = User(
            email='user1@example.com', first_name='User1',
            password=generate_hash('Password1'))

        user2 = User(
            email='user2@example.com', first_name='User2',
            password=generate_hash('password2'))

        # Create cars
        car1 = Car(
            image='ferrariF512TR3', car_name='Ferrari F512 TR', make='Ferrari',
            model='F512 TR', year=1991, body_type='2-door berlinetta', horsepower=422,
            monthly_payment=3245.32, mileage=198978, like_count=11)
        
        car2 = Car(
            image='astonMartinSILagonda1', car_name='Aston Martin Lagonda Series 1', 
            make='Aston Martin', model='Lagonda', year=1974, body_type='4-door saloon', 
            horsepower=280, monthly_payment=4611.96, mileage=18324, like_count=14)
        
        car3 = Car(
            image='countachLP400Lamborghini1', car_name='Lamborghini Countach LP400', 
            make='Lamborghini', model='LP400', year=1974, body_type='2-door coupe', 
            horsepower=375, monthly_payment=8042.47, mileage=167228, like_count=86)
                
        db.session.add_all([user1, user2, car1, car2, car3])
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            print("\tTest data already exists in database.")
            return

        # User interactions
        #   User 1 likes Car 1 & 2, dislikes Car 3
        #   User 2 has not interacted with any cars
        interaction1 = UserInteraction(
            user_id=user1.id, car_id=car1.id, swiped_right=True)
        interaction2 = UserInteraction(
            user_id=user1.id, car_id=car2.id, swiped_right=True)
        interaction3 = UserInteraction(
            user_id=user1.id, car_id=car3.id, swiped_right=False)

        db.session.add_all([interaction1, interaction2, interaction3])
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            print("\tTest data already exists in database.")
            return


    def tearDown(self):
        """
        Ensures that the database is emptied for next unit test

        :return: None
        """
        with app.app_context():
            db.session.remove()
            db.drop_all()


    
    # Authentication tests
    def login_test_user(self):
        """
        Logs in the test user using valid credentials

        Testing for:
        - Successful login
        - Successful login flash message
        """
        with self.app as client:
            # Login the test user
            user_data = {'email': 'user1@example.com', 'password': 'Password1'}
            login_response = client.post('/login', data=user_data, follow_redirects=True)
        
            with app.app_context():
                user = db.session.get(User, 1)
                self.assertIsNotNone(user, "Test user not found in database")
                
                # Check if login was successful
                self.assertEqual(login_response.status_code, 200)
                self.assertIn('Home', login_response.get_data(as_text=True))
                self.assertIn('Signed in successfully!', login_response.get_data(as_text=True))
    
    
    def login_test_user_fail(self):
        """
        Logs in the test user using invalid credentials

        Testing for:
        - Unsuccessful login
        - Unsuccessful login flash message
        """
        with self.app as client:
            # Login the test user
            user_data = {'email': 'user1@example.com', 'password': None}
            login_response = client.post(
                '/login', data=user_data, follow_redirects=False)

            with app.app_context():
                user = db.session.get(User, 1)
                self.assertIsNotNone(user, "Test user not found in database")

                # Check if login was unsuccessful
                self.assertEqual(login_response.status_code, 200)
                self.assertIn('Incorrect email or password, try again.',
                              login_response.get_data(as_text=True))

    
    def test_route_user_signup(self):
        """
        Signs up the test user using valid credentials

        Testing for:
        - Successful signup
        - Successful signup flash message
        """
        with app.app_context():
            valid_data = {
                'email': 'new@example.com',
                'first_name': 'New',
                'password': 'Newpassword1',
                'confirm_password': 'Newpassword1'
            }

            # Test registration with valid data
            response = self.app.post('/signup',
                                     data=valid_data, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Account created!", 
                response.get_data(as_text=True))


    def test_route_user_signup_fail(self):
        """
        Signs up the test user using invalid credentials

        Testing for:
        - Unsuccessful signup
        - Unsuccessful signup flash message
        """
        with app.app_context():
            invalid_data = {
                'email': 'new@example.com',
                'first_name': 'New',
                'password': None,
                'confirm_password': 'Newpassword1'
            }

            # Test registration with invalid data
            response = self.app.post('/signup',
                                     data=invalid_data, follow_redirects=True)
            self.assertIn("Sign Up", response.get_data(as_text=True))
 
    
    def logout_test_user(self):
        """
        Logs out the test user

        Testing for:
        - Successful logout
        - Successful logout flash message
        """
        # Log in the test user
        self.login_test_user()

        with app.app_context():
            # Check if user is logged in
            response = self.app.get('/logout', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            # Check if logout was successful
            self.assertIn('Signed out successfully!',
                          response.get_data(as_text=True))



    #   Form tests
    def test_login_form_validation(self):
        """
        Form validation tests for the login form

        Testing for:
        - Valid input
        - Invalid email
        - Invalid password (empty)
        """
        with app.app_context():
            # Base valid data
            base_data = {'email': 'user@example.com',
                         'password': 'ValidPass123'}

            # Test valid input
            form = LoginForm(data=base_data)
            self.assertTrue(form.validate())

            # Test invalid email
            invalid_email_data = base_data.copy()
            invalid_email_data['email'] = 'invalid-email'
            form = LoginForm(data=invalid_email_data)
            self.assertFalse(form.validate())

            # Test invalid (empty) password
            empty_pwd_data = base_data.copy()
            empty_pwd_data['password'] = ''
            form = LoginForm(data=empty_pwd_data)
            self.assertFalse(form.validate())


    def test_registration_form_validation(self):
        """
        Form validation tests for the registration form

        Testing for:
        - Valid input
        - Invalid (mismatch) password
        - Invalid (too long) password
        - Invalid (missing num/chars) password
        - Invalid first name (contains numbers)
        - Invalid first name (empty)
        """
        with app.app_context():
            # Base valid data
            base_data = {
                'email': 'newUser@example.com',
                'first_name': 'NewUser',
                'password': 'ValidPass123',
                'confirm_password': 'ValidPass123'
            }

            # Test valid input
            form = RegistrationForm(data=base_data)
            self.assertTrue(form.validate())

            # Test invalid (mismatch) password 1
            mismatch_pwd_data = base_data.copy()
            mismatch_pwd_data['confirm_password'] = 'DifferentPass123'
            form = RegistrationForm(data=mismatch_pwd_data)
            self.assertFalse(form.validate())

            # Test invalid (too long) password 2
            overflow_pwd_data = base_data.copy()
            overflow_pwd_data['password'] = f"{'.' * 19}"
            form = RegistrationForm(data=overflow_pwd_data)
            self.assertFalse(form.validate())

            # Test invalid (missing num/chars) password 3
            weak_pwd_data = base_data.copy()
            weak_pwd_data['password'] = 'weakpassword'
            form = RegistrationForm(data=weak_pwd_data)
            self.assertFalse(form.validate())

            # Test invalid first name (contains numbers) 1
            num_first_name_data = base_data.copy()
            num_first_name_data['first_name'] = 'NewUser1'
            form = RegistrationForm(data=num_first_name_data)
            self.assertFalse(form.validate())

            # Test invalid first name (empty) 2
            empty_first_name_data = base_data.copy()
            empty_first_name_data['first_name'] = ''
            form = RegistrationForm(data=empty_first_name_data)
            self.assertFalse(form.validate())


    
    # Model tests
    #   Creation tests
    def test_valid_car_creation(self):
        """
        Tests the existence of the test car from setup()
        """
        with app.app_context():
            car1_id = db.session.get(Car, 1).id
            self.assertIsNotNone(car1_id)
    

    def test_invalid_car_creation(self):
        """
        Creates an invalid car
        
        Testing for:
        - Invalid car object in database
        """
        with app.app_context():
            car = Car(make='', model='', year=1900, like_count=0)
            db.session.add(car)

            with self.assertRaises(Exception):
                db.session.commit()
            
            self.assertIsNone(car.id)


    def test_valid_user_creation(self):
        """
        Tests the existence of the test user from setup()
        """
        with app.app_context():
            user1_id = db.session.get(User, 1).id
            self.assertIsNotNone(user1_id)

  
    def test_invalid_user_creation(self):
        """
        Creates an invalid user

        Testing for:
        - Invalid user object in database
        """
        with app.app_context():
            user_id = User(email='', first_name='', password='').id
            self.assertIsNone(user_id)


    def test_valid_user_interaction_creation(self):
        """
        Tests the existence of the test user interaction from setup()
        """
        with app.app_context():
            interaction1_id = db.session.get(UserInteraction, 1).id
            self.assertIsNotNone(interaction1_id)


    def test_invalid_user_interaction_creation(self):
        """
        Creates an invalid user interaction

        Testing for:
        - Invalid user interaction object in database
        """
        with app.app_context():
            interaction = UserInteraction(
                user_id=1, car_id=3, swiped_right=None)
            db.session.add(interaction)

            with self.assertRaises(Exception):
                db.session.commit()
            
            self.assertIsNone(interaction.id)
    

    #   Deletion tests
    def test_delete_user(self):
        """
        Tests the deletion of the test user 2 from setup()

        Testing for:
        - User 2 deleted from database
        - User 2 no longer exists in database
        """
        with app.app_context():
            # Confirm that 2 users exist to begin with
            users = User.query.all()
            user_count = len(users)
            self.assertEqual(user_count, 2)

            user2 = db.session.get(User, 2)
            self.assertIsNotNone(user2)
        
            db.session.delete(user2)
            db.session.commit()

            # Check if user 2 exists
            new_user2 = db.session.get(User, 2)
            self.assertIsNone(new_user2)

            # Double check if user 2 was deleted
            new_users = User.query.all()
            new_user_count = len(new_users)
            self.assertEqual(new_user_count, user_count - 1)

    
    def test_delete_user_interactions(self):
        """
        Deletes all interactions for user 1

        Testing for:
        - All interactions for user 1 deleted from database
        - All interactions for user 1 no longer exist in database
        """
        with app.app_context():
            # Confirm that 3 interactions exist for user 1 to begin with
            interactions = UserInteraction.query.filter_by(user_id=1).all()
            interaction_count = len(interactions)
            self.assertEqual(interaction_count, 3)

            # Delete interaction 3 for user 1
            interaction3 = db.session.get(UserInteraction, 3)
            self.assertIsNotNone(interaction3)

            db.session.delete(interaction3)
            db.session.commit()

            # Check if interaction 3 exists
            new_interaction3 = db.session.get(UserInteraction, 3)
            self.assertIsNone(new_interaction3)

            # Double check if interaction 3 was deleted
            new_interactions = UserInteraction.query.filter_by(user_id=1).all()
            new_interaction_count = len(new_interactions)
            self.assertEqual(new_interaction_count, interaction_count - 1)
    

    def test_delete_account_route(self):
        """
        Tests the deletion of the test user 1 from setup() 
            through the delete_account route

        Testing for:
        - User 1 deleted from database
        - User 1 no longer exists in database
        """
        # Log in the test user
        self.login_test_user()

        with app.app_context():
            response = self.app.post('/delete_account', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            # self.assertIn('Logged Out', response.get_data(as_text=True))

            # Verify that the user is actually deleted
            user = db.session.get(User, 1)
            self.assertIsNone(user)


    #   Model relationship tests
    def test_valid_user_interaction_relationship(self):
        """
        Tests the relationship between user 1 and interaction 1

        Testing for:
        - User 1 and interaction 1 are related
        - User 1 and interaction 1 are not related to user 2 or car 1
        """
        with app.app_context():
            # Retrieve user 1 from the database
            user1 = User.query.first()
            self.assertIsNotNone(user1, "Test user not found in database")

            # Retrieve car 1 from the database
            car1 = Car.query.first()
            self.assertIsNotNone(car1, "Test car not found in database")

            # Retrieve interaction 1 from the database
            test_interaction = UserInteraction.query.first()
            self.assertIsNotNone(test_interaction, "Test interaction not found in database")

            # Test the user 1 interaction relationship
            self.assertEqual(test_interaction.user, user1)

    
    def test_invalid_user_interaction_relationship(self):
        """
        Tests the relationship between user 2 and interaction 1

        Testing for:
        - User 2 and interaction 1 are not related
        - User 2 and interaction 1 are not related to user 1 or car 1
        """

        with app.app_context():
            # Retrieve user 2 from the database
            user2 = db.session.get(User, 2)
            self.assertIsNotNone(user2, "User 2 not found in database")

            # Retrieve car 1 from the database
            car1 = db.session.get(Car, 1)
            self.assertIsNotNone(car1, "Car 1 not found in database")

            # Retrieve all interactions from the database
            interactions = UserInteraction.query.all()
            self.assertIsNotNone(interactions, "No interactions found in database")

            # Test the user interaction relationship
            # This should fail because user 2 and none of the cars are related
            # because user 2 has not interacted with any cars.
            for interaction in interactions:
                self.assertNotEqual(interaction.user, user2)
    

 
    # Live-service tests
    def test_like_count_increment(self):
        """
        Tests the incrementation of the like count for car 1

        Testing for:
        - Like count incremented by 1
        """
        with app.app_context():
            # Retrieve the test car from the database (entry 1)
            car1 = Car.query.first()
            self.assertIsNotNone(car1, "Car 1 not found in database")

            # Save the car ID and like count for the test
            car1_id = car1.id
            before_increment = car1.like_count

            # Simulate the AJAX call to increment like count
            response = self.app.post(
                f'/toggle_count/{car1_id}', json={'liked': True})
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['like_count'], before_increment + 1)

            # Re-query the car to get the updated like count
            car1 = db.session.get(Car, 1)
            self.assertEqual(car1.like_count, before_increment + 1)


    def test_like_count_decrement(self):
        """
        Tests the decrementation of the like count for car 1

        Testing for:
        - Like count decremented by 1
        """
        with app.app_context():
            # Retrieve the test car from the database
            car1 = Car.query.first()
            self.assertIsNotNone(car1, "Car 1 not found in database")

            # Save the car ID and like count for the test
            car1_id = car1.id
            before_decrement = car1.like_count

            # Simulate the AJAX call to increment like count
            response = self.app.post(
                f'/toggle_count/{car1_id}', json={'liked': False})
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['like_count'], before_decrement - 1)

            # Re-query the car to get the updated like count
            car1 = db.session.get(Car, 1)
            self.assertEqual(car1.like_count, before_decrement - 1)


    def test_invalid_like_count_action(self):
        """
        Tests the invalidation of the like count for car 1

        Testing for:
        - Like count unchanged
        """
        with app.app_context():
            # Retrieve the test car from the database
            car1 = Car.query.first()
            self.assertIsNotNone(car1, "Car 1 not found in database")

            # Save the car ID and like count for the test
            car1_id = car1.id
            before_decrement = car1.like_count

            # Simulate the invalid AJAX call JSON response
            response = self.app.post(
                f'/toggle_count/{car1_id}', json={'liked': None})
            data = response.get_json()
            self.assertEqual(response.status_code, 400)
            self.assertNotEqual(list(data.keys())[0], 'liked')

            # Re-query the car to get the unchanged like count
            car1 = db.session.get(Car, 1)
            self.assertEqual(car1.like_count, before_decrement)


    def test_cards_depleted(self):
        """
        Tests the cards depleted signal

        Testing for:
        - Cards depleted signal received
        - Cards not depleted signal received
        - Invalid cards depleted signal received
        - Flash messages received
        """
        with app.app_context():
            # Simulate a valid 'cards depleted' signal
            base_data = {'isEmpty': True}

            response = self.app.post(
                '/cards-depleted',
                json=base_data
            )
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['message'], "No more cards available")

            # Simulate another valid 'cards not depleted' signal
            cards_full_data = base_data.copy()
            cards_full_data['isEmpty'] = False
            response = self.app.post(
                '/cards-depleted',
                json=cards_full_data
            )
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['message'], "Cards still available")

            # Simulate an invalid 'cards depleted' signal
            invalid_card_data = base_data.copy()
            invalid_card_data.clear()
            response = self.app.post(
                '/cards-depleted',
                json=invalid_card_data
            )
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertEqual(data['error'], "Invalid request")


    def test_reaction_validation(self):
        """
        Tests the validation of the reaction data/signal

        Testing for:
        - Valid reaction data/signal
        - Invalid reaction data/signal (empty)
        - Invalid reaction data/signal (missing car ID)
        - Invalid reaction data/signal (missing swiped_right)
        """

        # Log in the test user
        self.login_test_user()

        with app.app_context():
            # Valid data
            base_data = {'carID': 1, 'swiped_right': True}
            response = self.app.post('/react', json=base_data)
            self.assertEqual(response.status_code, 200)
            self.assertIn('success', response.get_json()['status'])

            # Invalid data (empty)
            empty_reaction_data = base_data.copy()
            empty_reaction_data.clear()
            response = self.app.post('/react', json=empty_reaction_data)
            self.assertEqual(response.status_code, 400)
            self.assertIn('Invalid car ID and swiped_right provided',
                          response.get_json()['status'])

            # Invalid data (missing car ID)
            invalid_car_id = base_data.copy()
            invalid_car_id['carID'] = None
            response = self.app.post(
                '/react', json=invalid_car_id)
            self.assertEqual(response.status_code, 400)
            self.assertIn('Invalid car ID provided',
                          response.get_json()['status'])

            # Invalid data (missing swiped_right)
            invalid_swipe_action = base_data.copy()
            invalid_swipe_action['swiped_right'] = None
            response = self.app.post('/react', json=invalid_swipe_action)
            self.assertEqual(response.status_code, 400)
            self.assertIn('Invalid swiped_right provided',
                          response.get_json()['status'])


    def test_successful_login_resets_attempts(self):
        """
        Tests the reset of login attempts after a successful login

        Testing for:
        - Successful login
        - Successful login flash message
        - Login attempts reset to 0
        """
        invalid_data = {
            'email': 'user1@example.com',
            'password': 'mypassword'
        }

        with app.test_client() as client:
            # Show number of login attempts at start of session
            with client.session_transaction() as sess:
                attempts = sess.get('login_attempts', 0)
                self.assertEqual(attempts, 0)
            
            # Simulate a failed login attempt
            client.post('/login', data=invalid_data)
            with client.session_transaction() as sess:
                # Now 1
                attempts = sess.get('login_attempts', 0)
                self.assertEqual(attempts, 1)

            # Simulate a successful login
            valid_data = invalid_data.copy()
            valid_data['password'] = 'Password1'
            response = client.post('/login', 
                data=valid_data, follow_redirects=True)
            
            with client.session_transaction() as sess:
                # Reset to 0
                attempts = sess.get('login_attempts', 0)
                self.assertEqual(attempts, 0)
                self.assertIn('Home', response.get_data(as_text=True))
    

    def test_max_login_attempts_reached(self):
        """
        Tests the max login attempts reached signal

        Testing for:
        - Max login attempts reached signal received
        - Max login attempts not reached signal received
        - Invalid max login attempts reached signal received
        - Flash messages received
        """
        invalid_data = {
            'email': 'B@example.com',
            'password': 'Incorrect123'
        }
        with app.test_client() as client:
        # Show number of login attempts at start of session
            with client.session_transaction() as sess:
                attempts = sess.get('login_attempts', 0)
                self.assertEqual(attempts, 0)

            # Simulate the max number of allowed failed login attempts
            for _ in range(MAX_LOGIN_ATTEMPTS):
                client.post('/login', data=invalid_data)
            
            with client.session_transaction() as sess:
                # Now 3
                attempts = sess.get('login_attempts', 0)
                self.assertEqual(attempts, MAX_LOGIN_ATTEMPTS)

            # The next attempt should redirect to /signup and flash a msg
            response = client.post('/login', 
                data=invalid_data, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('Signup', response.get_data(as_text=True))
            self.assertIn('Maximum sign-in attempts reached.',
                          response.get_data(as_text=True))
    

    def test_login_attempts_increment(self):
        """
        Tests the incrementation of login attempts after failed logins

        Testing for:
        - Failed login attempt
        - Login attempts incremented by 1
        """

        # Using valid form data but incorrect credentials
        invalid_data = {
            'email': 'B@example.com',
            'password': 'Incorrect123'
        }
        
        with app.test_client() as client:
        # Show number of login attempts at start of session
            with client.session_transaction() as sess:
                attempts = sess.get('login_attempts', 0)
                self.assertEqual(attempts, 0)

            # Simulate first failed login attempt
            client.post('/login', data=invalid_data)
            with client.session_transaction() as sess:
                # Now 1
                attempts = sess.get('login_attempts', 0)
                self.assertEqual(attempts, 1)

            # Simulate second failed login attempt
            client.post('/login', data=invalid_data)
            with client.session_transaction() as sess:
                # Now 2
                attempts = sess.get('login_attempts', 0)
                self.assertEqual(attempts, 2)


    
    # Site route tests
    def test_home_route_as_guest(self):
        """
        Tests the home route as a guest

        Testing for:
        - Successful home route
        - Successful home route flash message
        """
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Welcome to AutoSwipe, Guest.', response.get_data(as_text=True))
    

    def test_home_route_as_user(self):
        """
        Tests the home route as a user

        Testing for:
        - Successful home route
        - Successful home route flash message
        """

        # Log in the test user
        self.login_test_user()

        with app.app_context():
            # Get the test user's first name
            name = db.session.get(User, 1).first_name
            self.assertIsNotNone(name)

            # Test the home route
            response = self.app.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'Welcome to AutoSwipe, {name}.', response.get_data(as_text=True))
    

    def test_routes_as_guest(self):
        """
        Tests the routes that require a user to be logged in

        Testing for:
        - Successful route redirect
        - Successful route flash message
        """
        # Test the routes that require a user to be logged in
        routes = ['/explore', '/saved', '/settings']

        for route in routes:
            response = self.app.get(route, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Sign In', response.get_data(as_text=True))


    def test_explore_route(self):
        """
        Tests the explore route

        Testing for:
        - Successful explore route
        - Successful explore route flash message
        """
        # Log in the test user
        self.login_test_user() 

        response = self.app.get('/explore')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Explore', response.get_data(as_text=True))
    

    def test_saved_route(self):
        """
        Tests the saved route

        Testing for:
        - Successful saved route
        - Successful saved route flash message
        """
        # Log in the test user
        self.login_test_user()
        response = self.app.get('/saved')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Saved', response.get_data(as_text=True))
    

    def test_single_view_route(self):
        """
        Tests the single view route

        Testing for:
        - Successful single view route
        - Successful single view route flash message
        """
        self.login_test_user()
        car_id = 1
        response = self.app.get(f'/saved/single-view/{car_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Single View', response.get_data(as_text=True))
    

    def test_settings_route(self):
        """
        Tests the settings route

        Testing for:
        - Successful settings route
        - Successful settings route flash message
        """
        # Log in the test user
        self.login_test_user()
        response = self.app.get('/settings')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Settings', response.get_data(as_text=True))
    
    
    #   Error page tests
    def test_404_page(self):
        """
        Tests the 404 page

        Testing for:
        - Successful 404 page
        - Successful 404 page flash message
        """
        response = self.app.get(
            '/this-route-does-not-exist', follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        self.assertIn('404', response.get_data(as_text=True))

    def test_500_page(self):
        """
        Tests the 500 page through the react route

        Testing for:
        - Successful 500 page
        - Successful 500 page flash message
        """
        # Log in the test user
        self.login_test_user()

        with app.app_context():
            with patch('app.views.db.session.commit') as mock_commit:
                mock_commit.side_effect = IntegrityError('', '', '')
                response = self.app.post(
                    '/react', json={'carID': 1, 'swiped_right': True})
                self.assertEqual(response.status_code, 500)
                self.assertIn('Unable to commit', response.get_json()['status'])
    

if __name__ == '__main__':
    unittest.main()
