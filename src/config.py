import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', '103.82.24.7'),
        'user': os.environ.get('DB_USER', 'mmddllg_huehub'),
        'password': os.environ.get('DB_PASS', 'Ngoctruong123@'),
        'database': os.environ.get('DB_NAME', 'mmddllg_fbstorea')
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 2592000  # 30 days in seconds
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
