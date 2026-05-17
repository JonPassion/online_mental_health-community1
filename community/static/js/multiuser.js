// Multi-User Chat System - Real-time Features
class MultiUserChat {
    constructor() {
        this.currentUser = null;
        this.onlineUsers = new Map();
        this.notifications = [];
        this.presenceInterval = null;
        this.notificationInterval = null;
        this.currentRoom = null;
        
        this.init();
    }
    
    init() {
        // Start presence tracking
        this.startPresenceTracking();
        
        // Start notification polling
        this.startNotificationPolling();
        
        // Set up event listeners
        this.setupEventListeners();
        
        console.log('Multi-user chat system initialized');
    }
    
    startPresenceTracking() {
        // Update presence every 30 seconds
        this.presenceInterval = setInterval(() => {
            this.updatePresence();
        }, 30000);
        
        // Initial presence update
        this.updatePresence();
    }
    
    updatePresence() {
        const formData = new FormData();
        if (this.currentRoom) {
            formData.append('room_id', this.currentRoom);
        }
        formData.append('activity_type', 'active');
        
        fetch('/users/api/update-presence/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Presence updated');
            }
        })
        .catch(error => console.error('Error updating presence:', error));
    }
    
    startNotificationPolling() {
        // Check notifications every 10 seconds
        this.notificationInterval = setInterval(() => {
            this.fetchNotifications();
        }, 10000);
        
        // Initial notification fetch
        this.fetchNotifications();
    }
    
    fetchNotifications() {
        fetch('/users/api/notifications/')
        .then(response => response.json())
        .then(data => {
            if (data.notifications && data.notifications.length > 0) {
                this.handleNewNotifications(data.notifications);
            }
        })
        .catch(error => console.error('Error fetching notifications:', error));
    }
    
    handleNewNotifications(notifications) {
        notifications.forEach(notif => {
            if (!this.isNotificationShown(notif.id)) {
                this.showNotification(notif);
                this.markNotificationRead(notif.id);
            }
        });
    }
    
    showNotification(notification) {
        // Show browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/static/img/notification-icon.png'
            });
        }
        
        // Show in-app notification
        this.showInAppNotification(notification);
    }
    
    showInAppNotification(notification) {
        const notificationEl = document.createElement('div');
        notificationEl.className = 'notification-toast';
        notificationEl.innerHTML = `
            <div class="notification-content">
                <strong>${notification.title}</strong>
                <p>${notification.message}</p>
                <small>${this.formatTime(notification.created_at)}</small>
            </div>
            <button onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(notificationEl);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notificationEl.parentElement) {
                notificationEl.remove();
            }
        }, 5000);
    }
    
    markNotificationRead(notificationId) {
        fetch(`/users/api/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        });
    }
    
    fetchOnlineUsers() {
        fetch('/users/api/online-users/')
        .then(response => response.json())
        .then(data => {
            this.updateOnlineUsers(data.online_users);
        })
        .catch(error => console.error('Error fetching online users:', error));
    }
    
    updateOnlineUsers(users) {
        this.onlineUsers.clear();
        users.forEach(user => {
            this.onlineUsers.set(user.id, user);
        });
        
        this.updateOnlineUsersUI();
    }
    
    updateOnlineUsersUI() {
        // Update user cards with online status
        document.querySelectorAll('.user-card').forEach(card => {
            const userId = parseInt(card.dataset.userid);
            const user = this.onlineUsers.get(userId);
            
            const statusEl = card.querySelector('.user-status');
            if (statusEl) {
                if (user) {
                    statusEl.className = 'user-status online';
                    statusEl.title = `Online - In ${user.current_room || 'system'}`;
                } else {
                    statusEl.className = 'user-status offline';
                    statusEl.title = 'Offline';
                }
            }
        });
    }
    
    setupEventListeners() {
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        
        // Update room when chat changes
        window.addEventListener('chatRoomChanged', (e) => {
            this.currentRoom = e.detail.roomId;
            this.updatePresence();
        });
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }
    
    cleanup() {
        if (this.presenceInterval) {
            clearInterval(this.presenceInterval);
        }
        if (this.notificationInterval) {
            clearInterval(this.notificationInterval);
        }
    }
    
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
    
    isNotificationShown(notificationId) {
        return this.notifications.includes(notificationId);
    }
}

// Initialize the multi-user system
let multiUserChat = null;

document.addEventListener('DOMContentLoaded', function() {
    multiUserChat = new MultiUserChat();
    
    // Custom event for room changes
    window.openChat = function(type, name, roomId) {
        // Call existing openChat function
        if (typeof originalOpenChat === 'function') {
            originalOpenChat(type, name, roomId);
        }
        
        // Emit custom event
        window.dispatchEvent(new CustomEvent('chatRoomChanged', {
            detail: { type, name, roomId }
        }));
    };
    
    // Fetch online users periodically
    setInterval(() => {
        if (multiUserChat) {
            multiUserChat.fetchOnlineUsers();
        }
    }, 15000);
});
