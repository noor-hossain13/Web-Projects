from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio
from models import db
from models.video_call import VideoCall
from datetime import datetime
from flask import request


@socketio.on('join_room')
def handle_join_room(data):
    """User joins a video call room"""
    room_id = data['room_id']
    username = data['username']
    
    join_room(room_id)
    
    # Update call status to active
    video_call = VideoCall.query.filter_by(room_id=room_id).first()
    if video_call and video_call.status == 'waiting':
        video_call.status = 'active'
        video_call.started_at = datetime.utcnow()
        db.session.commit()
    
    emit('user_joined', {
        'username': username,
        'message': f'{username} joined the call'
    }, room=room_id)
    
    print(f'{username} joined room {room_id}')

@socketio.on('leave_room')
def handle_leave_room(data):
    """User leaves a video call room"""
    room_id = data['room_id']
    username = data['username']
    
    leave_room(room_id)
    
    emit('user_left', {
        'username': username,
        'message': f'{username} left the call'
    }, room=room_id)
    
    print(f'{username} left room {room_id}')

@socketio.on('offer')
def handle_offer(data):
    """Handle WebRTC offer"""
    room_id = data['room_id']
    emit('offer', data, room=room_id, skip_sid=request.sid)

@socketio.on('answer')
def handle_answer(data):
    """Handle WebRTC answer"""
    room_id = data['room_id']
    emit('answer', data, room=room_id, skip_sid=request.sid)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    """Handle ICE candidate"""
    room_id = data['room_id']
    emit('ice_candidate', data, room=room_id, skip_sid=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnect"""
    print('User disconnected')