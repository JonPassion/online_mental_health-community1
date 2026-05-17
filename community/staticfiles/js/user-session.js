// User Differentiation and Session Management
class UserSessionManager {
    constructor() {
        this.currentUser = null;
        this.currentUserId = null;
        this.activeRooms = new Map();
        this.userSessions = new Map();
        this.init();
    }
    
    init() {
        // Get current user info from page
        this.currentUser = this.getCurrentUser();
        this.currentUserId = this.getCurrentUserId();
        
        if (!this.currentUserId) {
            console.error('User not authenticated');
            return;
        }
        
        console.log(`User session initialized for: ${this.currentUser} (ID: ${this.currentUserId})`);
        
        // Set up user-specific storage
        this.setupUserStorage();
        
        // Start session monitoring
        this.startSessionMonitoring();
    }
    
    getCurrentUser() {
        // Try to get current user from various sources
        const userElements = document.querySelectorAll('[data-current-user]');
        if (userElements.length > 0) {
            return userElements[0].dataset.currentUser;
        }
        
        // Fallback to page title or other indicators
        const title = document.title;
        const match = title.match(/Dashboard\s*-\s*(\w+)/);
        return match ? match[1] : null;
    }
    
    getCurrentUserId() {
        // Try to get user ID from page data
        const userIdElements = document.querySelectorAll('[data-current-user-id]');
        if (userIdElements.length > 0) {
            return parseInt(userIdElements[0].dataset.currentUserId);
        }
        
        // Fallback: try to extract from URL or other sources
        return null;
    }
    
    setupUserStorage() {
        // Create user-specific storage keys
        this.storageKeys = {
            messages: `chat_messages_${this.currentUserId}`,
            activeRooms: `active_rooms_${this.currentUserId}`,
            userPreferences: `user_prefs_${this.currentUserId}`,
            lastActivity: `last_activity_${this.currentUserId}`
        };
    }
    
    startSessionMonitoring() {
        // Monitor user activity and prevent mixing
        setInterval(() => {
            this.validateSession();
            this.cleanupMixedData();
        }, 5000);
    }
    
    validateSession() {
        // Ensure we're still the same user
        const storedUserId = localStorage.getItem(this.storageKeys.lastActivity);
        if (storedUserId && storedUserId !== this.currentUserId.toString()) {
            console.warn('User session mismatch detected!');
            this.clearMixedData();
        }
        
        // Update last activity
        localStorage.setItem(this.storageKeys.lastActivity, this.currentUserId.toString());
    }
    
    cleanupMixedData() {
        // Clean up any mixed user data
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith('chat_messages_') && key !== this.storageKeys.messages) {
                console.log(`Cleaning up mixed data: ${key}`);
                localStorage.removeItem(key);
            }
        });
    }
    
    clearMixedData() {
        // Clear all potentially mixed data
        this.cleanupMixedData();
        
        // Reset current session
        this.activeRooms.clear();
        this.userSessions.clear();
        
        console.log('Mixed data cleared, session reset');
    }
    
    addRoomToSession(roomId, roomName) {
        // Track room for current user only
        this.activeRooms.set(roomId, {
            name: roomName,
            joinedAt: new Date().toISOString(),
            userId: this.currentUserId
        });
        
        // Save to user-specific storage
        localStorage.setItem(this.storageKeys.activeRooms, JSON.stringify([...this.activeRooms]));
    }
    
    removeRoomFromSession(roomId) {
        this.activeRooms.delete(roomId);
        localStorage.setItem(this.storageKeys.activeRooms, JSON.stringify([...this.activeRooms]));
    }
    
    isCurrentUserMessage(messageUserId) {
        return parseInt(messageUserId) === this.currentUserId;
    }
    
    getUserMessageClass(messageUserId) {
        return this.isCurrentUserMessage(messageUserId) ? 'my-message' : 'other-message';
    }
    
    formatMessageUsername(username, messageUserId) {
        if (this.isCurrentUserMessage(messageUserId)) {
            return 'You';
        }
        return username;
    }
}

// Enhanced message handling with user differentiation
class MessageHandler {
    constructor(sessionManager) {
        this.sessionManager = sessionManager;
        this.messageCache = new Map();
    }
    
    addMessage(roomId, message) {
        // Only process message if it belongs to current user's session
        if (!this.validateMessageOwnership(message)) {
            console.warn('Ignoring message from different user session');
            return false;
        }
        
        // Cache message for this room
        if (!this.messageCache.has(roomId)) {
            this.messageCache.set(roomId, []);
        }
        
        this.messageCache.get(roomId).push(message);
        
        // Display message with proper user differentiation
        this.displayMessage(message);
        
        return true;
    }
    
    validateMessageOwnership(message) {
        // Check if message is relevant to current user
        if (message.user_id && !this.sessionManager.isCurrentUserMessage(message.user_id)) {
            // It's from another user, that's fine
            return true;
        }
        
        // For sent messages, ensure they're from current user
        return true;
    }
    
    displayMessage(message) {
        const chatBox = document.getElementById('chatBox');
        if (!chatBox) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${this.sessionManager.getUserMessageClass(message.user_id)}`;
        messageDiv.dataset.messageId = message.id;
        messageDiv.dataset.userId = message.user_id;
        
        const messageContent = `
            <div class="message-header">
                <strong>${this.sessionManager.formatMessageUsername(message.user, message.user_id)}</strong>
                <span class="message-time">${this.formatTime(message.timestamp)}</span>
            </div>
            <div class="message-content">${message.content}</div>
        `;
        
        messageDiv.innerHTML = messageContent;
        chatBox.appendChild(messageDiv);
        
        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    clearRoomMessages(roomId) {
        // Clear messages for specific room
        this.messageCache.delete(roomId);
        
        // Clear UI
        const chatBox = document.getElementById('chatBox');
        if (chatBox) {
            chatBox.innerHTML = '';
        }
    }
}

// Initialize the user session management
let sessionManager = null;
let messageHandler = null;

document.addEventListener('DOMContentLoaded', function() {
    sessionManager = new UserSessionManager();
    messageHandler = new MessageHandler(sessionManager);
    
    // Override global functions to use session management
    window.originalLoadMessages = window.loadMessages;
    
    window.loadMessages = async function() {
        if (!sessionManager.currentUserId) {
            console.error('Cannot load messages: User not authenticated');
            return;
        }
        
        try {
            const response = await fetch(`/chat/chat/messages/${window.currentRoomId}/`);
            if (response.ok) {
                const messages = await response.json();
                
                // Clear existing messages
                messageHandler.clearRoomMessages(window.currentRoomId);
                
                // Add messages with user differentiation
                messages.forEach(message => {
                    messageHandler.addMessage(window.currentRoomId, message);
                });
                
                console.log(`Loaded ${messages.length} messages for user ${sessionManager.currentUser}`);
            }
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    };
    
    // Override send message to include user validation
    window.originalSendChatMessage = window.sendChatMessage;
    
    window.sendChatMessage = async function() {
        if (!sessionManager.currentUserId) {
            console.error('Cannot send message: User not authenticated');
            return;
        }
        
        const input = document.getElementById('chatInput');
        const msg = input.value.trim();
        if (!msg || !window.currentRoomId) return;
        
        try {
            const response = await fetch('/chat/chat/send/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: `room_id=${window.currentRoomId}&message=${encodeURIComponent(msg)}`
            });
            
            if (response.ok) {
                const message = await response.json();
                
                // Add message with proper user differentiation
                if (messageHandler.addMessage(window.currentRoomId, message)) {
                    input.value = '';
                    console.log(`Message sent by user ${sessionManager.currentUser}`);
                }
            } else {
                console.error('Failed to send message');
            }
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };
});
