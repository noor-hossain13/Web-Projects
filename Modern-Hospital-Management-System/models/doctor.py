from models import db
from datetime import datetime

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer, default=0)
    available_time = db.Column(db.String(200))
    qualification = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic')
    prescriptions = db.relationship('Prescription', backref='doctor', lazy='dynamic')
    
    def __repr__(self):
        return f'<Doctor {self.user.name} - {self.specialization}>'