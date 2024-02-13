from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
import re

# Constants for validation error messages
EMAIL_LEN_MSG = "ERROR: Enter an E-mail between 2 and 20 characters long."
NAME_LEN_MSG = "ERROR: Enter a name between 5 and 30 characters long."
PWD_LEN_MSG = "ERROR: Password must be between 7 and 18 characters long."
PWD_MATCH_MSG = "ERROR: Passwords must match."
NAME_CHARS_ONLY_MSG = "ERROR: Name must contain only letters."
PWD_LETTERS_NUMBERS_MSG = "ERROR: Password must include both letters and numbers."


class BaseUserForm(FlaskForm):
    """
    A base form for user-related operations.

    Attributes:
        email (StringField): Email field with required validation and email format checking.
    
    Methods:
        validate_email:
            Normalizes email input to lowercase.
    """
    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(min=5, max=30, message=EMAIL_LEN_MSG)])

    def validate_email(form, field):
        """
        Validate and normalize the email field.

        Parameters:
            form: The instance of the form where the field exists.
            field: The field to be validated and normalized.

        Returns:
            None: The field data is modified in place.
        """
        # Normalize email to lowercase
        field.data = field.data.lower()


class LoginForm(BaseUserForm):
    """
    A form for handling user login.

    Inherits from BaseUserForm and adds password and submit fields.

    Attributes:
        password (PasswordField): Password field with required validation.
        submit (SubmitField): Submit button for the form.
    """
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegistrationForm(BaseUserForm):
    """
    A form for handling user registration.

    Inherits from BaseUserForm and adds first name, password, confirm password, and submit fields.

    Attributes:
        first_name (StringField): First name field with required validation and length constraints.
        password (PasswordField): Password field with required validation and length constraint.
        confirm_password (PasswordField): Confirm password field with required validation and matching constraint.
        submit (SubmitField): Submit button for the form.

    Methods:
        validate_first_name:
            Validates that the first name contains only letters.
    """
    first_name = StringField('First Name', validators=[
                             DataRequired(), Length(min=2, max=20, message=NAME_LEN_MSG)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=7, max=18, message=PWD_LEN_MSG)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message=PWD_MATCH_MSG)
    ])
    submit = SubmitField('Sign Up')

    def validate_first_name(form, field):
        """
        Custom validation method for the first name field.

        Parameters:
            form: The instance of the form where the field exists.
            field: The field to be validated.

        Raises:
            ValidationError: If the first name does not contain only letters.
        """
        if not field.data.isalpha():
            raise ValidationError(NAME_CHARS_ONLY_MSG)
        
    def validate_password(form, field):
        """
        Custom validation method for the password field to ensure it includes both letters and numbers.

        Parameters:
            form: The instance of the form where the field exists.
            field: The field to be validated.

        Raises:
            ValidationError: If the password does not contain both letters and numbers.
        """
        if not re.search(r"[a-zA-Z]", field.data) or not re.search(r"[0-9]", field.data) or not (7 <= len(field.data) <= 18):
            raise ValidationError(PWD_LETTERS_NUMBERS_MSG)
