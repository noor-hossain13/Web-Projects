from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db
from models.video_call import VideoCall
from models.appointment import Appointment
from models.doctor import Doctor
from models.patient import Patient
import uuid
from datetime import datetime

video_bp = Blueprint('video', __name__, url_prefix='/video')

@video_bp.route('/start/<int:appointment_id>')
@login_required
def start_call(appointment_id):
    """Start or join a video call for an appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify user has access to this appointment
    if current_user.role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if not doctor or appointment.doctor_id != doctor.id:
            flash('Unauthorized access!', 'error')
            return redirect(url_for('doctor.appointments'))
    elif current_user.role == 'patient':
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if not patient or appointment.patient_id != patient.id:
            flash('Unauthorized access!', 'error')
            return redirect(url_for('patient.appointments'))
    else:
        flash('Access denied!', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if video call already exists
    video_call = VideoCall.query.filter_by(
        appointment_id=appointment_id, 
        status='active'
    ).first()
    
    if not video_call:
        # Check for waiting calls
        video_call = VideoCall.query.filter_by(
            appointment_id=appointment_id, 
            status='waiting'
        ).first()
        
        if not video_call:
            # Create new video call room
            room_id = str(uuid.uuid4())
            video_call = VideoCall(
                appointment_id=appointment_id,
                room_id=room_id,
                initiated_by=current_user.id,
                status='waiting'
            )
            db.session.add(video_call)
            db.session.commit()
    
    return render_template('video_call.html', 
                         video_call=video_call,
                         appointment=appointment,
                         is_doctor=current_user.role == 'doctor')

@video_bp.route('/end/<int:call_id>', methods=['POST'])
@login_required
def end_call(call_id):
    """End a video call"""
    video_call = VideoCall.query.get_or_404(call_id)
    
    video_call.status = 'ended'
    video_call.ended_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Call ended'})

@video_bp.route('/history')
@login_required
def call_history():
    """View video call history"""
    if current_user.role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    elif current_user.role == 'patient':
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    else:
        flash('Access denied!', 'error')
        return redirect(url_for('auth.login'))
    
    appointment_ids = [a.id for a in appointments]
    video_calls = VideoCall.query.filter(
        VideoCall.appointment_id.in_(appointment_ids)
    ).order_by(VideoCall.created_at.desc()).all()
    
    return render_template('video_call_history.html', video_calls=video_calls)