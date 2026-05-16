import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///hospital.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Create upload directories
    REPORTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'reports')
    PRESCRIPTIONS_FOLDER = os.path.join(UPLOAD_FOLDER, 'prescriptions')