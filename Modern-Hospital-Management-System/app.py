from flask import Flask, render_template
from flask_login import LoginManager
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from config import Config
from models import db
from models.user import User
from utils.database import init_db, bcrypt
from routes import register_blueprints
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
bcrypt.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database
init_db(app)

# Create upload folders
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
os.makedirs(app.config['PRESCRIPTIONS_FOLDER'], exist_ok=True)

# Register blueprints
register_blueprints(app)

# ============================================
# Socket.IO Events for Real-time Chat
# ============================================

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        print(f'User {current_user.name} connected')

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{current_user.name} has joined the chat.'}, room=room)

@socketio.on('send_message')
def handle_message(data):
    from models.message import Message
    from models import db
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=data['receiver_id'],
        content=data['message']
    )
    db.session.add(message)
    db.session.commit()
    
    room = data['room']
    emit('receive_message', {
        'message': data['message'],
        'sender': current_user.name,
        'sender_id': current_user.id,
        'timestamp': message.timestamp.strftime('%H:%M')
    }, room=room)

# ============================================
# Socket.IO Events for Video Calls (WebRTC)
# ============================================

@socketio.on('join_video_room')
def handle_join_video_room(data):
    """User joins a video call room"""
    room_id = data['room_id']
    username = data['username']
    
    join_room(room_id)
    
    # Update video call status to active
    from models.video_call import VideoCall
    from datetime import datetime
    
    video_call = VideoCall.query.filter_by(room_id=room_id).first()
    if video_call and video_call.status == 'waiting':
        video_call.status = 'active'
        video_call.started_at = datetime.utcnow()
        db.session.commit()
    
    emit('user_joined', {
        'username': username,
        'message': f'{username} joined the call'
    }, room=room_id)
    
    print(f'{username} joined video room {room_id}')

@socketio.on('leave_video_room')
def handle_leave_video_room(data):
    """User leaves a video call room"""
    room_id = data['room_id']
    username = data['username']
    
    leave_room(room_id)
    
    emit('user_left', {
        'username': username,
        'message': f'{username} left the call'
    }, room=room_id)
    
    print(f'{username} left video room {room_id}')

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """Handle WebRTC offer for video call"""
    room_id = data['room_id']
    print(f'WebRTC offer received for room {room_id}')
    emit('webrtc_offer', data, room=room_id, include_self=False)

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    """Handle WebRTC answer for video call"""
    room_id = data['room_id']
    print(f'WebRTC answer received for room {room_id}')
    emit('webrtc_answer', data, room=room_id, include_self=False)

@socketio.on('webrtc_ice_candidate')
def handle_ice_candidate(data):
    """Handle ICE candidate for WebRTC connection"""
    room_id = data['room_id']
    print(f'ICE candidate received for room {room_id}')
    emit('webrtc_ice_candidate', data, room=room_id, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnect"""
    if current_user.is_authenticated:
        print(f'User {current_user.name} disconnected')

# ============================================
# Run Application
# ============================================

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
#How to Run it 
#First give permission by windows power shell by running the command
#Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#\venv\Scripts\Activate.ps1.
#always check mysql in xampp
