import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', 'your_firebase_api_key')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN', 'your_project_id.firebaseapp.com')
    FIREBASE_DB_URL = os.environ.get('FIREBASE_DB_URL', 'https://your_project_id.firebaseio.com')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'your_project_id.appspot.com')
    FIREBASE_SERVICE_ACCOUNT_KEY = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY', 'path/to/serviceAccountKey.json')