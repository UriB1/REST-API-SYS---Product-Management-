import re

from functools import wraps
from flask import request, jsonify


def validate_email_format(email):
    """
    Validates if the email is in a correct format.
    
    Args:
        email (str): The email address to validate.
    
    Returns:
        bool: True if valid, False otherwise.
    """

    if not isinstance(email, str):
        raise ValueError("Email must be a string")
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def validate_password_strength(password: str) -> bool:
    """
    Validates if the password is strong.
    
    The password must:
    - Be at least 8 characters long.
    - Include uppercase, lowercase, digit, and special character.
    - Have no spaces.
    
    Args:
        password (str): The password to validate.
    
    Returns:
        bool: True if strong, False otherwise.
    """

    if len(password) < 8:
        return False
    if not re.search(r'(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>])', password):
        return False
    if re.search(r'\s', password):
        return False
    return True

def auth_required(auth_client):
    """
    Decorator to enforce authentication using a token.
    
    Args:
        auth_client: Client for validating the token.
    
    Returns:
        Decorated function that checks the Authorization token in headers.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Authorization token is missing or invalid'}), 401
            token = auth_header.split(' ')[1]
            try:
                user = auth_client.verify_id_token(token)
                request.user = user
            except Exception as e:
                return jsonify({'error': 'Invalid or expired token'}), 401
            return f(*args, **kwargs)
        return decorated_function
    return decorator