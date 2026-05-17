// Inbox Management System
class InboxManager {
    constructor() {
        this.conversations = [];
        this.filteredConversations = [];
        this.init();
    }
    
    init() {
        // Load inbox when page loads
        this.loadInbox();
        
        // Auto-refresh inbox every 30 seconds
        setInterval(() => {
            this.loadInbox();
        }, 30000);
    }
    
    async loadInbox() {
        try {
            const response = await fetch('/chat/api/inbox/');
            if (response.ok) {
                const data = await response.json();
                this.conversations = data.conversations || [];
                this.filteredConversations = [...this.conversations];
                this.renderInbox();
                console.log(`Loaded ${this.conversations.length} conversations`);
            } else {
                console.error('Failed to load inbox');
                this.showEmptyInbox();
            }
        } catch (error) {
            console.error('Error loading inbox:', error);
            this.showEmptyInbox();
        }
    }
    
    renderInbox() {
        const container = document.getElementById('inboxConversations');
        if (!container) return;
        
        if (this.filteredConversations.length === 0) {
            this.showEmptyInbox();
            return;
        }
        
        const inboxHTML = this.filteredConversations.map(conv => this.createConversationHTML(conv)).join('');
        container.innerHTML = inboxHTML;
        
        // Update unread count in tab
        this.updateUnreadCount();
    }
    
    createConversationHTML(conversation) {
        const hasUnread = conversation.unread_count > 0;
        const unreadBadge = hasUnread ? `<span class="unread-badge">${conversation.unread_count}</span>` : '';
        const unreadClass = hasUnread ? 'unread' : '';
        
        const avatar = conversation.other_username.charAt(0).toUpperCase();
        const timeAgo = this.formatTimeAgo(conversation.latest_timestamp);
        const messagePreview = conversation.latest_message.length > 30 
            ? conversation.latest_message.substring(0, 30) + '...' 
            : conversation.latest_message;
        
        return `
            <div class="conversation-item ${unreadClass}" 
                 onclick="window.openConversation(${conversation.room_id}, '${conversation.other_username}')"
                 data-user-id="${conversation.other_user_id}"
                 data-room-id="${conversation.room_id}"
                 style="cursor: pointer;">
                <div class="conversation-avatar">
                    ${avatar}
                    ${hasUnread ? '<div class="user-status online"></div>' : ''}
                </div>
                <div class="conversation-content">
                    <div class="conversation-name">${conversation.other_username}</div>
                    <div class="conversation-message">${messagePreview}</div>
                </div>
                <div class="conversation-meta">
                    <div class="conversation-time">${timeAgo}</div>
                    ${unreadBadge}
                </div>
            </div>
        `;
    }
    
    formatTimeAgo(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }
    
    showEmptyInbox() {
        const container = document.getElementById('inboxConversations');
        if (container) {
            container.innerHTML = '<div class="no-conversations">No conversations yet. Start messaging users from the Users tab!</div>';
        }
    }
    
    updateUnreadCount() {
        const totalUnread = this.conversations.reduce((sum, conv) => sum + conv.unread_count, 0);
        const inboxTab = document.querySelector('[onclick="openTab(\'inbox\')"]');
        
        if (inboxTab && totalUnread > 0) {
            inboxTab.innerHTML = `Inbox <span class="unread-badge">${totalUnread}</span>`;
        } else if (inboxTab) {
            inboxTab.innerHTML = 'Inbox';
        }
    }
    
    async openFullConversation(userId, username, roomId) {
        try {
            // Use the new WhatsApp-style conversation view
            if (typeof openConversation === 'function') {
                openConversation(roomId, username);
            } else {
                console.error('openConversation function not found');
            }
            
            // Mark as read and refresh inbox
            await this.markConversationAsRead(userId);
            
            console.log(`Opened conversation with ${username}`);
        } catch (error) {
            console.error('Error loading conversation:', error);
        }
    }
    
    loadConversationMessages(messages) {
        const chatBox = document.getElementById('chatBox');
        if (!chatBox) return;
        
        // Clear existing messages
        chatBox.innerHTML = '';
        
        // Add all messages with proper user differentiation
        messages.forEach(message => {
            const messageDiv = document.createElement('div');
            const isMyMessage = message.user_id === window.sessionManager?.currentUserId;
            
            messageDiv.className = `message ${isMyMessage ? 'my-message' : 'other-message'}`;
            messageDiv.dataset.messageId = message.id;
            messageDiv.dataset.userId = message.user_id;
            
            const messageContent = `
                <div class="message-header">
                    <strong>${isMyMessage ? 'You' : message.user}</strong>
                    <span class="message-time">${this.formatMessageTime(message.timestamp)}</span>
                </div>
                <div class="message-content">${message.content}</div>
            `;
            
            messageDiv.innerHTML = messageContent;
            chatBox.appendChild(messageDiv);
        });
        
        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
        
        console.log(`Loaded ${messages.length} messages in conversation`);
    }
    
    formatMessageTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    async markConversationAsRead(userId) {
        try {
            // This would be an API call to mark messages as read
            // For now, we'll just reload the inbox
            setTimeout(() => {
                this.loadInbox();
            }, 1000);
        } catch (error) {
            console.error('Error marking conversation as read:', error);
        }
    }
    
    filterConversations(searchTerm) {
        if (!searchTerm) {
            this.filteredConversations = [...this.conversations];
        } else {
            const term = searchTerm.toLowerCase();
            this.filteredConversations = this.conversations.filter(conv => 
                conv.other_username.toLowerCase().includes(term) ||
                conv.latest_message.toLowerCase().includes(term)
            );
        }
        this.renderInbox();
    }
    
    refresh() {
        this.loadInbox();
    }
}

// Global functions for HTML onclick handlers
function refreshInbox() {
    if (window.inboxManager) {
        window.inboxManager.refresh();
    }
}

function filterInbox() {
    const searchInput = document.getElementById('inboxSearchInput');
    if (window.inboxManager && searchInput) {
        window.inboxManager.filterConversations(searchInput.value);
    }
}

// Initialize inbox manager when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.inboxManager = new InboxManager();
    
    // Override openTab to load inbox when switching to inbox tab
    const originalOpenTab = window.openTab;
    window.openTab = function(tabName) {
        originalOpenTab(tabName);
        
        if (tabName === 'inbox' && window.inboxManager) {
            window.inboxManager.loadInbox();
        }
    };
});
