from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import db
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.prescription import Prescription
from datetime import datetime, date

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'patient':
            flash('Access denied. Patients only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@patient_bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    # Initialize default values
    appointments = []
    stats = {
        'upcoming': 0,
        'pending': 0,
        'completed': 0,
        'total_doctors': 0
    }
    
    if patient:
        try:
            # Get recent appointments
            appointments = Appointment.query.filter_by(
                patient_id=patient.id
            ).order_by(Appointment.date.desc()).limit(5).all()
            
            # Calculate statistics
            stats['pending'] = Appointment.query.filter_by(
                patient_id=patient.id,
                status='pending'
            ).count()
            
            stats['upcoming'] = Appointment.query.filter(
                Appointment.patient_id == patient.id,
                Appointment.status == 'approved',
                Appointment.date >= date.today()
            ).count()
            
            stats['completed'] = Appointment.query.filter_by(
                patient_id=patient.id,
                status='completed'
            ).count()
            
            # Count unique doctors patient has visited
            stats['total_doctors'] = db.session.query(Appointment.doctor_id).filter(
                Appointment.patient_id == patient.id
            ).distinct().count()
            
        except Exception as e:
            print(f"Error loading dashboard stats: {e}")
            flash('Error loading dashboard data', 'warning')
    
    return render_template('patient_dashboard.html', 
                         patient=patient, 
                         appointments=appointments,
                         stats=stats)  # <-- This is the key: passing stats to the template

@patient_bp.route('/profile')
@login_required
@patient_required
def profile():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    return render_template('patient_profile.html', patient=patient)

@patient_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@patient_required
def edit_profile():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient:
        flash('Patient profile not found.', 'error')
        return redirect(url_for('patient.dashboard'))
    
    if request.method == 'POST':
        patient.phone = request.form.get('phone')
        patient.address = request.form.get('address')
        patient.dob = request.form.get('dob')
        patient.blood_group = request.form.get('blood_group')
        patient.gender = request.form.get('gender')
        current_user.name = request.form.get('name')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
        
        return redirect(url_for('patient.profile'))
    
    return render_template('patient_edit_profile.html', patient=patient)

@patient_bp.route('/doctors')
@login_required
@patient_required
def doctors():
    doctors_list = Doctor.query.filter_by(is_approved=True).all()
    return render_template('patient_doctors.html', doctors=doctors_list)

@patient_bp.route('/doctor/<int:doctor_id>')
@login_required
@patient_required
def doctor_profile(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if not doctor.is_approved:
        flash('This doctor is not available.', 'warning')
        return redirect(url_for('patient.doctors'))
    
    return render_template('patient_doctor_detail.html', doctor=doctor)

@patient_bp.route('/book-appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@patient_required
def book_appointment(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient:
        flash('Patient profile not found. Please complete your profile first.', 'warning')
        return redirect(url_for('patient.profile'))
    
    if not doctor.is_approved:
        flash('This doctor is not available for appointments.', 'warning')
        return redirect(url_for('patient.doctors'))
    
    if request.method == 'POST':
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason = request.form.get('reason')
        
        if not appointment_date or not appointment_time or not reason:
            flash('Please fill in all required fields.', 'error')
            return render_template('patient_book_appointment.html', 
                                 doctor=doctor,
                                 today=date.today().isoformat())
        
        # Convert string date and time to proper format
        try:
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(appointment_time, '%H:%M').time()
            
            # Validate date is not in the past
            if date_obj < date.today():
                flash('Cannot book appointments in the past.', 'error')
                return render_template('patient_book_appointment.html', 
                                     doctor=doctor,
                                     today=date.today().isoformat())
            
        except ValueError:
            flash('Invalid date or time format.', 'error')
            return render_template('patient_book_appointment.html', 
                                 doctor=doctor,
                                 today=date.today().isoformat())
        
        # Create new appointment
        new_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            date=date_obj,
            time=time_obj,
            reason=reason,
            status='pending'
        )
        
        try:
            db.session.add(new_appointment)
            db.session.commit()
            flash('Appointment booked successfully! Waiting for doctor approval.', 'success')
            return redirect(url_for('patient.appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error booking appointment: {str(e)}', 'error')
    
    # Pass today's date to template
    return render_template('patient_book_appointment.html', 
                         doctor=doctor,
                         today=date.today().isoformat())
                         
@patient_bp.route('/appointments')
@login_required
@patient_required
def appointments():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient:
        flash('Patient profile not found.', 'warning')
        return redirect(url_for('patient.dashboard'))
    
    status_filter = request.args.get('status', 'all')
    query = Appointment.query.filter_by(patient_id=patient.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    appointments_list = query.order_by(Appointment.date.desc()).all()
    
    return render_template('patient_appointments.html', 
                         appointments=appointments_list,
                         status_filter=status_filter)

@patient_bp.route('/appointment/<int:appointment_id>')
@login_required
@patient_required
def appointment_detail(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient or appointment.patient_id != patient.id:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('patient.appointments'))
    
    return render_template('patient_appointment_detail.html', appointment=appointment)

@patient_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@patient_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient or appointment.patient_id != patient.id:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('patient.appointments'))
    
    if appointment.status in ['pending', 'approved']:
        appointment.status = 'cancelled'
        try:
            db.session.commit()
            flash('Appointment cancelled successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error cancelling appointment: {str(e)}', 'error')
    else:
        flash('Cannot cancel this appointment.', 'warning')
    
    return redirect(url_for('patient.appointments'))

@patient_bp.route('/prescriptions')
@login_required
@patient_required
def prescriptions():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient:
        flash('Patient profile not found.', 'warning')
        return redirect(url_for('patient.dashboard'))
    
    prescriptions_list = Prescription.query.filter_by(
        patient_id=patient.id
    ).order_by(Prescription.created_at.desc()).all()
    
    return render_template('patient_prescriptions.html', 
                         prescriptions=prescriptions_list)

@patient_bp.route('/prescription/<int:prescription_id>')
@login_required
@patient_required
def prescription_detail(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient or prescription.patient_id != patient.id:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('patient.prescriptions'))
    
    return render_template('patient_prescription_detail.html', 
                         prescription=prescription)

@patient_bp.route('/medical-records')
@login_required
@patient_required
def medical_records():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient:
        flash('Patient profile not found.', 'warning')
        return redirect(url_for('patient.dashboard'))
    
    appointments = Appointment.query.filter_by(
        patient_id=patient.id
    ).order_by(Appointment.date.desc()).all()
    
    prescriptions = Prescription.query.filter_by(
        patient_id=patient.id
    ).order_by(Prescription.created_at.desc()).all()
    
    return render_template('patient_medical_records.html', 
                         patient=patient,
                         appointments=appointments,
                         prescriptions=prescriptions)

@patient_bp.route('/reports')
@login_required
@patient_required
def reports():
    """View all medical reports"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient:
        flash('Patient profile not found.', 'warning')
        return redirect(url_for('patient.dashboard'))
    
    # Get all appointments with completed status (they might have reports)
    completed_appointments = Appointment.query.filter_by(
        patient_id=patient.id,
        status='completed'
    ).order_by(Appointment.date.desc()).all()
    
    # Get all prescriptions (these are like reports)
    prescriptions = Prescription.query.filter_by(
        patient_id=patient.id
    ).order_by(Prescription.created_at.desc()).all()
    
    return render_template('patient_reports.html', 
                         appointments=completed_appointments,
                         prescriptions=prescriptions,
                         patient=patient)