from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db
from models.doctor import Doctor
from models.appointment import Appointment
from models.prescription import Prescription
from models.patient import Patient
from models.notification import Notification
from functools import wraps
from datetime import datetime

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'doctor':
            flash('Access denied. Doctor only.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@doctor_bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    # Check if doctor profile exists
    if not doctor:
        flash('Doctor profile not found. Please contact administrator.', 'warning')
        return render_template('doctor_profile_incomplete.html')
    
    # Check if doctor is approved
    if not doctor.is_approved:
        return render_template('doctor_pending.html', doctor=doctor)
    
    # Calculate statistics
    pending = Appointment.query.filter_by(
        doctor_id=doctor.id, 
        status='pending'
    ).count()
    
    upcoming = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'approved',
        Appointment.date >= datetime.now().date()
    ).count()
    
    completed = Appointment.query.filter_by(
        doctor_id=doctor.id,
        status='completed'
    ).count()
    
    # Get recent appointments
    recent_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id
    ).order_by(Appointment.date.desc()).limit(5).all()
    
    # Get total unique patients
    total_patients = db.session.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.id
    ).distinct().count()
    
    stats = {
        'pending': pending,
        'upcoming': upcoming,
        'completed': completed,
        'total_patients': total_patients
    }
    
    return render_template('doctor_dashboard.html', 
                         doctor=doctor,
                         stats=stats,
                         recent_appointments=recent_appointments)

@doctor_bp.route('/appointments')
@login_required
@doctor_required
def appointments():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth.login'))
    
    status_filter = request.args.get('status', 'all')
    
    # Build query
    query = Appointment.query.filter_by(doctor_id=doctor.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    all_appointments = query.order_by(Appointment.date.desc()).all()
    
    return render_template('doctor_appointments.html', 
                         appointments=all_appointments,
                         status_filter=status_filter)

@doctor_bp.route('/appointment/<int:id>/update', methods=['POST'])
@login_required
@doctor_required
def update_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if not doctor or appointment.doctor_id != doctor.id:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('doctor.appointments'))
    
    action = request.form.get('action')
    
    if action == 'approve':
        appointment.status = 'approved'
        msg = 'Appointment approved!'
    elif action == 'reject':
        appointment.status = 'rejected'
        msg = 'Appointment rejected!'
    elif action == 'complete':
        appointment.status = 'completed'
        msg = 'Appointment marked as completed!'
    else:
        flash('Invalid action!', 'error')
        return redirect(url_for('doctor.appointments'))
    
    db.session.commit()
    
    # Send notification
    try:
        from utils.mailer import notify_appointment_status
        notify_appointment_status(appointment, appointment.status)
    except Exception as e:
        print(f"Notification error: {e}")
    
    flash(msg, 'success')
    return redirect(url_for('doctor.appointments'))

@doctor_bp.route('/prescription/add/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@doctor_required
def add_prescription(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if not doctor or appointment.doctor_id != doctor.id:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('doctor.dashboard'))
    
    if request.method == 'POST':
        prescription = Prescription(
            appointment_id=appointment.id,
            doctor_id=doctor.id,
            patient_id=appointment.patient_id,
            diagnosis=request.form.get('diagnosis'),
            medicines=request.form.get('medicines'),
            tests=request.form.get('tests'),
            notes=request.form.get('notes')
        )
        db.session.add(prescription)
        
        # Mark appointment as completed
        appointment.status = 'completed'
        db.session.commit()
        
        # Create notification for patient
        try:
            notification = Notification(
                user_id=appointment.patient.user_id,
                title='New Prescription',
                message=f'Dr. {doctor.user.name} has added a prescription for your appointment.',
                type='prescription'
            )
            db.session.add(notification)
            db.session.commit()
        except Exception as e:
            print(f"Notification error: {e}")
        
        flash('Prescription added successfully!', 'success')
        return redirect(url_for('doctor.appointments'))
    
    return render_template('add_prescription.html', appointment=appointment, doctor=doctor)

@doctor_bp.route('/prescriptions')
@login_required
@doctor_required
def prescriptions():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth.login'))
    
    all_prescriptions = Prescription.query.filter_by(
        doctor_id=doctor.id
    ).order_by(Prescription.created_at.desc()).all()
    
    return render_template('doctor_prescriptions.html', prescriptions=all_prescriptions)

@doctor_bp.route('/prescription/<int:id>')
@login_required
@doctor_required
def view_prescription(id):
    prescription = Prescription.query.get_or_404(id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if not doctor or prescription.doctor_id != doctor.id:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('doctor.prescriptions'))
    
    return render_template('prescription_detail.html', prescription=prescription)

@doctor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@doctor_required
def profile():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Update doctor profile
        doctor.specialization = request.form.get('specialization')
        doctor.experience = request.form.get('experience')
        doctor.qualification = request.form.get('qualification')
        doctor.phone = request.form.get('phone')
        doctor.available_time = request.form.get('available_time')
        
        # Update user name
        current_user.name = request.form.get('name')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
        
        return redirect(url_for('doctor.profile'))
    
    return render_template('doctor_profile.html', doctor=doctor)

@doctor_bp.route('/patients')
@login_required
@doctor_required
def patients():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get unique patients who have appointments with this doctor
    patient_ids = db.session.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.id
    ).distinct().all()
    
    patient_ids = [pid[0] for pid in patient_ids]
    patients_list = Patient.query.filter(Patient.id.in_(patient_ids)).all()
    
    return render_template('doctor_patients.html', patients=patients_list)

@doctor_bp.route('/patient/<int:patient_id>')
@login_required
@doctor_required
def patient_detail(patient_id):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    patient = Patient.query.get_or_404(patient_id)
    
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth.login'))
    
    # Verify this doctor has seen this patient
    has_appointment = Appointment.query.filter_by(
        doctor_id=doctor.id,
        patient_id=patient.id
    ).first()
    
    if not has_appointment:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('doctor.patients'))
    
    # Get patient's appointments with this doctor
    appointments = Appointment.query.filter_by(
        doctor_id=doctor.id,
        patient_id=patient.id
    ).order_by(Appointment.date.desc()).all()
    
    # Get prescriptions
    prescriptions = Prescription.query.filter_by(
        doctor_id=doctor.id,
        patient_id=patient.id
    ).order_by(Prescription.created_at.desc()).all()
    
    return render_template('doctor_patient_detail.html', 
                         patient=patient,
                         appointments=appointments,
                         prescriptions=prescriptions)