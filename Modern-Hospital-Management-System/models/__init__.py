from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Import all models
from .user import User
from .doctor import Doctor
from .patient import Patient
from .appointment import Appointment
from .prescription import Prescription
from .message import Message
from .report import Report
from .notification import Notification
from .ai_suggestion import AISuggestion