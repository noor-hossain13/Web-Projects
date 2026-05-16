// Real-time Chat Functionality
const socket = io();

// Join room when chat opens
function joinChatRoom(roomId) {
    socket.emit('join', { room: roomId });
}

// Send message
function sendMessage(receiverId, message, roomId) {
    socket.emit('send_message', {
        receiver_id: receiverId,
        message: message,
        room: roomId
    });
}

// Receive message
socket.on('receive_message', (data) => {
    addMessageToChat(data);
});

// Add message to chat UI
function addMessageToChat(data) {
    const chatContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${data.sender_id === currentUserId ? 'sent' : 'received'}`;
    
    messageDiv.innerHTML = `
        <div class="chat-bubble">
            <strong>${data.sender}</strong>
            <p>${data.message}</p>
            <small class="text-muted">${data.timestamp}</small>
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Initialize chat
document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (message) {
                const receiverId = document.getElementById('receiverId').value;
                const roomId = document.getElementById('roomId').value;
                sendMessage(receiverId, message, roomId);
                input.value = '';
            }
        });
    }
});