import os
from dotenv import load_dotenv

# Load environment variables from the .env file
# This allows us to use environment-specific settings without hardcoding them into the source code.
load_dotenv()

class Config:
    # Secret key for session management and cryptographic operations
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')  # Default value used if the environment variable is not set
    
    # Firebase configuration
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', 'your_firebase_api_key')  # API key for Firebase authentication
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN', 'your_project_id.firebaseapp.com')  # Firebase authentication domain
    FIREBASE_DB_URL = os.environ.get('FIREBASE_DB_URL', 'https://your_project_id.firebaseio.com')  # URL of the Firebase Realtime Database
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'your_project_id.appspot.com')  # URL of the Firebase Storage bucket
    FIREBASE_SERVICE_ACCOUNT_KEY = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY', 'path/to/serviceAccountKey.json')  # Path to the Firebase service account key file
