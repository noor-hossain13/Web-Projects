from models import db
from datetime import datetime

class VideoCall(db.Model):
    __tablename__ = 'video_calls'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    room_id = db.Column(db.String(100), unique=True, nullable=False)
    initiated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='waiting')  # waiting, active, ended
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointment = db.relationship('Appointment', backref='video_calls')
    initiator = db.relationship('User', foreign_keys=[initiated_by])
    
    def __repr__(self):
        return f'<VideoCall {self.room_id}>'