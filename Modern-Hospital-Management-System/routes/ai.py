from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.patient import Patient
from models.ai_suggestion import AISuggestion
from models import db
from utils.ai_helper import get_ai_response, get_health_advice, suggest_appointment_time
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/assistant')
@login_required
def assistant():
    """Render AI Assistant page"""
    return render_template('ai_assistant.html')

@ai_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages from user"""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Get AI response
    ai_response = get_ai_response(user_message)
    
    # Save suggestion if user is patient
    if current_user.role == 'patient':
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if patient:
            suggestion = AISuggestion(
                patient_id=patient.id,
                suggestion_text=ai_response,
                suggestion_type='chat',
                created_at=datetime.utcnow()
            )
            db.session.add(suggestion)
            db.session.commit()
    
    return jsonify({
        'response': ai_response,
        'timestamp': datetime.utcnow().isoformat()  # precise timestamp
    })

@ai_bp.route('/health_advice', methods=['POST'])
@login_required
def health_advice():
    """Get health advice from AI based on patient symptoms"""
    data = request.get_json()
    symptoms = data.get('symptoms', '').strip()
    
    if not symptoms:
        return jsonify({'error': 'No symptoms provided'}), 400
    
    advice = get_health_advice(symptoms)
    
    # Save for patient
    if current_user.role == 'patient':
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if patient:
            suggestion = AISuggestion(
                patient_id=patient.id,
                suggestion_text=advice,
                suggestion_type='health_tip',
                created_at=datetime.utcnow()
            )
            db.session.add(suggestion)
            db.session.commit()
    
    return jsonify({'advice': advice})

@ai_bp.route('/suggest_time/<int:doctor_id>')
@login_required
def suggest_time(doctor_id):
    """Suggest appointment times for a doctor"""
    from models.doctor import Doctor
    from models.appointment import Appointment
    from datetime import datetime, timedelta
    
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Get existing appointments for next 7 days
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=7)
    
    existing = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date.between(start_date, end_date),
        Appointment.status != 'cancelled'
    ).all()
    
    existing_slots = [f"{apt.date} {apt.time}" for apt in existing]
    
    suggestion = suggest_appointment_time(
        doctor_schedule=doctor.available_time or "9:00-17:00",
        existing_appointments=existing_slots
    )
    
    return jsonify({'suggestion': suggestion})
