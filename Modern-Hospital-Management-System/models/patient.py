from models import db
from datetime import datetime

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    blood_group = db.Column(db.String(5))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic')
    prescriptions = db.relationship('Prescription', backref='patient', lazy='dynamic')
    reports = db.relationship('Report', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    ai_suggestions = db.relationship('AISuggestion', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Patient {self.user.name}>'