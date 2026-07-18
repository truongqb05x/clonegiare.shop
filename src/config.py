import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fbstore_secret_key_fixed_2024')  # Use environment variable or fixed default
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', '103.82.24.7'),
        'user': os.environ.get('DB_USER', 'mmddllg_huehub'),
        'password': os.environ.get('DB_PASS', 'Ngoctruong123@'),
        'database': os.environ.get('DB_NAME', 'mmddllg_fbstorea')
    }
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 31536000  # 1 year in seconds
    SESSION_REFRESH_EACH_REQUEST = True
    SESSION_COOKIE_SECURE = False   # Set to True for production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_PATH = '/'
