from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.prescription import Prescription
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin only.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    pending_doctors = Doctor.query.filter_by(is_approved=False).count()
    
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all()
    pending_approvals = Doctor.query.filter_by(is_approved=False).all()
    
    stats = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'pending_doctors': pending_doctors
    }
    
    return render_template('admin_dashboard.html', 
                         stats=stats,
                         recent_appointments=recent_appointments,
                         pending_approvals=pending_approvals)

@admin_bp.route('/doctors')
@login_required
@admin_required
def doctors():
    all_doctors = Doctor.query.join(User).all()
    return render_template('admin_doctors.html', doctors=all_doctors)

@admin_bp.route('/approve_doctor/<int:doctor_id>', methods=['POST'])
@login_required
@admin_required
def approve_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_approved = True
    db.session.commit()
    
    from utils.mailer import create_notification
    create_notification(
        doctor.user_id,
        'Account Approved',
        'Congratulations! Your doctor account has been approved. You can now start managing appointments.',
        'approval'
    )
    
    flash(f'Doctor {doctor.user.name} approved successfully!', 'success')
    return redirect(url_for('admin.doctors'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot delete admin user!', 'error')
        return redirect(url_for('admin.dashboard'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.name} deleted successfully!', 'success')
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/patients')
@login_required
@admin_required
def patients():
    all_patients = Patient.query.join(User).all()
    return render_template('admin_patients.html', patients=all_patients)

@admin_bp.route('/appointments')
@login_required
@admin_required
def appointments():
    all_appointments = Appointment.query.order_by(Appointment.date.desc()).all()
    return render_template('admin_appointments.html', appointments=all_appointments)

@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    # Data for charts
    from sqlalchemy import func
    
    # Appointments by status
    status_data = db.session.query(
        Appointment.status,
        func.count(Appointment.id)
    ).group_by(Appointment.status).all()
    
    # Doctors by specialization
    spec_data = db.session.query(
        Doctor.specialization,
        func.count(Doctor.id)
    ).group_by(Doctor.specialization).all()
    
    return jsonify({
        'appointment_status': dict(status_data),
        'specializations': dict(spec_data)
    })