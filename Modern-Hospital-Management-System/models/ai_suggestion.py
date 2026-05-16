from models import db
from datetime import datetime

class AISuggestion(db.Model):
    __tablename__ = 'ai_suggestions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    suggestion_text = db.Column(db.Text, nullable=False)
    suggestion_type = db.Column(db.String(50))  # scheduling, health_tip, reminder
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AISuggestion {self.id} - {self.suggestion_type}>'