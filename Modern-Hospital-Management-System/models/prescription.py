from models import db
from datetime import datetime

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    diagnosis = db.Column(db.Text)
    medicines = db.Column(db.Text, nullable=False)
    tests = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships are defined via backrefs in other models:
    # - doctor: defined in Doctor model
    # - patient: defined in Patient model  
    # - appointment: defined in Appointment model
    
    def __repr__(self):
        return f'<Prescription {self.id} - Patient: {self.patient_id}>'