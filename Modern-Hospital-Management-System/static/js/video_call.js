// Load configuration
var configData = JSON.parse(document.getElementById('config-data').textContent);
var ROOM_ID = configData.room_id;
var USERNAME = configData.username;
var IS_DOCTOR = configData.is_doctor;
var CALL_ID = configData.call_id;
var INITIATED_BY_CURRENT_USER = configData.initiated_by_current_user;

// Initialize Socket.IO
var socket = io();

// WebRTC Configuration
var configuration = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};

var localStream;
var remoteStream;
var peerConnection;
var isVideoEnabled = true;
var isAudioEnabled = true;

// DOM Elements
var localVideo = document.getElementById('localVideo');
var remoteVideo = document.getElementById('remoteVideo');
var connectionStatus = document.getElementById('connectionStatus');
var callStatus = document.getElementById('callStatus');
var toggleVideoBtn = document.getElementById('toggleVideo');
var toggleAudioBtn = document.getElementById('toggleAudio');
var endCallBtn = document.getElementById('endCall');
var toggleFullscreenBtn = document.getElementById('toggleFullscreen');

// Initialize
function init() {
    navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
    })
    .then(function(stream) {
        localStream = stream;
        localVideo.srcObject = localStream;
        
        socket.emit('join_video_room', {
            room_id: ROOM_ID,
            username: USERNAME
        });
        
        updateConnectionStatus('connected');
    })
    .catch(function(error) {
        console.error('Error accessing media devices:', error);
        alert('Could not access camera/microphone. Please grant permissions and try again.');
    });
}

// Create peer connection
function createPeerConnection() {
    peerConnection = new RTCPeerConnection(configuration);
    
    localStream.getTracks().forEach(function(track) {
        peerConnection.addTrack(track, localStream);
    });
    
    peerConnection.ontrack = function(event) {
        if (!remoteStream) {
            remoteStream = new MediaStream();
            remoteVideo.srcObject = remoteStream;
        }
        remoteStream.addTrack(event.track);
    };
    
    peerConnection.onicecandidate = function(event) {
        if (event.candidate) {
            socket.emit('webrtc_ice_candidate', {
                room_id: ROOM_ID,
                candidate: event.candidate
            });
        }
    };
    
    peerConnection.onconnectionstatechange = function() {
        console.log('Connection state:', peerConnection.connectionState);
        if (peerConnection.connectionState === 'connected') {
            updateConnectionStatus('connected');
            callStatus.textContent = 'Active';
            callStatus.className = 'badge bg-success';
        }
    };
}

// Socket event handlers
socket.on('user_joined', function(data) {
    console.log('User joined:', data);
    
    var participantsList = document.getElementById('participants');
    var li = document.createElement('li');
    li.innerHTML = '<i class="fas fa-user"></i> ' + data.username;
    participantsList.appendChild(li);
    
    if (IS_DOCTOR || INITIATED_BY_CURRENT_USER) {
        createPeerConnection();
        peerConnection.createOffer()
            .then(function(offer) {
                return peerConnection.setLocalDescription(offer);
            })
            .then(function() {
                socket.emit('webrtc_offer', {
                    room_id: ROOM_ID,
                    offer: peerConnection.localDescription
                });
            });
    }
});

socket.on('webrtc_offer', function(data) {
    console.log('Received offer');
    createPeerConnection();
    
    peerConnection.setRemoteDescription(data.offer)
        .then(function() {
            return peerConnection.createAnswer();
        })
        .then(function(answer) {
            return peerConnection.setLocalDescription(answer);
        })
        .then(function() {
            socket.emit('webrtc_answer', {
                room_id: ROOM_ID,
                answer: peerConnection.localDescription
            });
        });
});

socket.on('webrtc_answer', function(data) {
    console.log('Received answer');
    peerConnection.setRemoteDescription(data.answer);
});

socket.on('webrtc_ice_candidate', function(data) {
    console.log('Received ICE candidate');
    peerConnection.addIceCandidate(data.candidate)
        .catch(function(error) {
            console.error('Error adding ICE candidate:', error);
        });
});

socket.on('user_left', function(data) {
    console.log('User left:', data);
    alert(data.message);
    var redirectUrl = IS_DOCTOR ? '/doctor/appointments' : '/patient/appointments';
    window.location.href = redirectUrl;
});

// Control functions
function updateConnectionStatus(status) {
    var statusMap = {
        'connecting': '<i class="fas fa-circle text-warning"></i> Connecting...',
        'connected': '<i class="fas fa-circle text-success"></i> Connected',
        'disconnected': '<i class="fas fa-circle text-danger"></i> Disconnected'
    };
    connectionStatus.innerHTML = statusMap[status] || statusMap['connecting'];
}

toggleVideoBtn.onclick = function() {
    isVideoEnabled = !isVideoEnabled;
    localStream.getVideoTracks()[0].enabled = isVideoEnabled;
    toggleVideoBtn.innerHTML = isVideoEnabled ? 
        '<i class="fas fa-video"></i>' : 
        '<i class="fas fa-video-slash"></i>';
    toggleVideoBtn.classList.toggle('btn-danger');
};

toggleAudioBtn.onclick = function() {
    isAudioEnabled = !isAudioEnabled;
    localStream.getAudioTracks()[0].enabled = isAudioEnabled;
    toggleAudioBtn.innerHTML = isAudioEnabled ? 
        '<i class="fas fa-microphone"></i>' : 
        '<i class="fas fa-microphone-slash"></i>';
    toggleAudioBtn.classList.toggle('btn-danger');
};

endCallBtn.onclick = function() {
    if (confirm('Are you sure you want to end this call?')) {
        if (localStream) {
            localStream.getTracks().forEach(function(track) {
                track.stop();
            });
        }
        
        if (peerConnection) {
            peerConnection.close();
        }
        
        socket.emit('leave_video_room', {
            room_id: ROOM_ID,
            username: USERNAME
        });
        
        fetch('/video/end/' + CALL_ID, { method: 'POST' })
            .then(function() {
                var redirectUrl = IS_DOCTOR ? '/doctor/appointments' : '/patient/appointments';
                window.location.href = redirectUrl;
            });
    }
};

toggleFullscreenBtn.onclick = function() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
        toggleFullscreenBtn.innerHTML = '<i class="fas fa-compress"></i>';
    } else {
        document.exitFullscreen();
        toggleFullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
    }
};

// Initialize on page load
init();

// Cleanup on page unload
window.onbeforeunload = function() {
    if (localStream) {
        localStream.getTracks().forEach(function(track) {
            track.stop();
        });
    }
    if (peerConnection) {
        peerConnection.close();
    }
};