from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models.message import Message
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

def can_chat_with(user1_id, user2_id):
    """
    Check if two users can chat with each other
    Rules:
    - Admin can chat with anyone
    - Doctor and Patient can only chat if they have a COMPLETED appointment together
    """
    user1 = User.query.get(user1_id)
    user2 = User.query.get(user2_id)
    
    if not user1 or not user2:
        return False
    
    # Admin can chat with anyone
    if user1.role == 'admin' or user2.role == 'admin':
        return True
    
    # Check if one is doctor and one is patient
    if (user1.role == 'doctor' and user2.role == 'patient') or \
       (user1.role == 'patient' and user2.role == 'doctor'):
        
        # Find the doctor and patient
        if user1.role == 'doctor':
            doctor = Doctor.query.filter_by(user_id=user1_id).first()
            patient = Patient.query.filter_by(user_id=user2_id).first()
        else:
            doctor = Doctor.query.filter_by(user_id=user2_id).first()
            patient = Patient.query.filter_by(user_id=user1_id).first()
        
        if not doctor or not patient:
            return False
        
        # Check if they have any COMPLETED appointments
        completed_appointment = Appointment.query.filter_by(
            doctor_id=doctor.id,
            patient_id=patient.id,
            status='completed'
        ).first()
        
        return completed_appointment is not None
    
    return False

def get_authorized_contacts():
    """Get list of users current user can chat with based on completed appointments"""
    contacts = []
    
    if current_user.role == 'patient':
        # Get doctors with completed appointments
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if patient:
            completed_appointments = Appointment.query.filter_by(
                patient_id=patient.id,
                status='completed'
            ).all()
            
            doctor_ids = list(set([apt.doctor_id for apt in completed_appointments]))
            if doctor_ids:
                doctors = Doctor.query.filter(Doctor.id.in_(doctor_ids)).all()
                contacts = [d.user for d in doctors]
                
    elif current_user.role == 'doctor':
        # Get patients with completed appointments
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if doctor:
            completed_appointments = Appointment.query.filter_by(
                doctor_id=doctor.id,
                status='completed'
            ).all()
            
            patient_ids = list(set([apt.patient_id for apt in completed_appointments]))
            if patient_ids:
                patients = Patient.query.filter(Patient.id.in_(patient_ids)).all()
                contacts = [p.user for p in patients]
                
    elif current_user.role == 'admin':
        # Admin can chat with everyone
        contacts = User.query.filter(User.id != current_user.id).all()
    
    return contacts

@chat_bp.route('/')
@login_required
def index():
    # Get authorized contacts based on completed appointments
    authorized_contacts = get_authorized_contacts()
    authorized_ids = [c.id for c in authorized_contacts]
    
    # Get all users this user has chatted with
    sent = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id).distinct()
    received = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id).distinct()
    
    contact_ids = set([r[0] for r in sent] + [r[0] for r in received])
    
    # Filter to only show authorized contacts
    if current_user.role != 'admin':
        contact_ids = contact_ids.intersection(set(authorized_ids))
    
    # Add authorized contacts who haven't chatted yet
    contact_ids.update(authorized_ids)
    
    if contact_ids:
        contacts = User.query.filter(User.id.in_(contact_ids)).all()
    else:
        contacts = []
    
    return render_template('chat.html', contacts=contacts)

@chat_bp.route('/with/<int:user_id>')
@login_required
def chat_with(user_id):
    # Check if user is authorized to chat with this person
    if not can_chat_with(current_user.id, user_id):
        flash('You can only chat after completing an appointment together.', 'warning')
        return redirect(url_for('chat.index'))
    
    other_user = User.query.get_or_404(user_id)
    
    # Get conversation history
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            db.and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp).all()
    
    # Mark messages as read
    Message.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    return render_template('chat_window.html', other_user=other_user, messages=messages)

@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not receiver_id or not content:
        return jsonify({'error': 'Invalid data'}), 400
    
    # Check if user is authorized to chat with this person
    if not can_chat_with(current_user.id, receiver_id):
        return jsonify({'error': 'You can only send messages after completing an appointment together'}), 403
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    try:
        from utils.mailer import create_notification
        create_notification(
            receiver_id,
            'New Message',
            f'{current_user.name} sent you a message',
            'message'
        )
    except Exception as e:
        print(f"Notification error: {e}")
    
    return jsonify({
        'success': True,
        'message_id': message.id,
        'timestamp': message.timestamp.strftime('%H:%M')
    })

@chat_bp.route('/history/<int:user_id>')
@login_required
def get_history(user_id):
    # Check if user is authorized to chat with this person
    if not can_chat_with(current_user.id, user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            db.and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp).all()
    
    return jsonify([{
        'id': msg.id,
        'content': msg.content,
        'sender_id': msg.sender_id,
        'sender_name': msg.sender.name,
        'timestamp': msg.timestamp.strftime('%H:%M'),
        'is_mine': msg.sender_id == current_user.id
    } for msg in messages])