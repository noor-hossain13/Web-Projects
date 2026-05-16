from models import db
from datetime import datetime

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    report_type = db.Column(db.String(50))  # lab_report, scan, xray, etc.
    uploaded_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Report {self.id} - {self.report_type}>'