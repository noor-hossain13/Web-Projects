from flask import current_app
from models import db
from models.notification import Notification

def create_notification(user_id, title, message, notification_type='general'):
    '''Create a notification for a user'''
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        status='unread'
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def notify_appointment_status(appointment, status):
    '''Notify patient about appointment status change'''
    messages = {
        'approved': 'Your appointment has been approved!',
        'rejected': 'Your appointment has been rejected. Please book another slot.',
        'completed': 'Your appointment has been completed. Check for prescriptions.',
        'cancelled': 'Your appointment has been cancelled.'
    }
    
    create_notification(
        user_id=appointment.patient.user_id,
        title='Appointment Update',
        message=f'{messages.get(status, "Appointment status updated")} - Dr. {appointment.doctor.user.name}',
        notification_type='appointment'
    )