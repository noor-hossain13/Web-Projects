// AI Assistant JavaScript
async function getAIResponse(message) {
    try {
        const response = await fetch('/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();
        return data.response;
    } catch (error) {
        console.error('Error:', error);
        return 'Sorry, I encountered an error. Please try again.';
    }
}

async function getHealthAdvice(symptoms) {
    try {
        const response = await fetch('/ai/health_advice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symptoms })
        });
        
        const data = await response.json();
        return data.advice;
    } catch (error) {
        console.error('Error:', error);
        return 'Unable to get health advice at this time.';
    }
}

// Notification checker
function checkNotifications() {
    fetch('/api/notifications/unread')
        .then(res => res.json())
        .then(data => {
            if (data.count > 0) {
                updateNotificationBadge(data.count);
            }
        })
        .catch(err => console.error('Notification check failed:', err));
}

function updateNotificationBadge(count) {
    const badge = document.getElementById('notificationBadge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline' : 'none';
    }
}

// Check notifications every 30 seconds
setInterval(checkNotifications, 30000);