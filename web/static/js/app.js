/**
 * Intel AI Assistant - Main Application
 * Handles real-time chat, WebSocket communication, and UI interactions
 */

class IntelAIAssistant {
    constructor() {
        this.websocket = null;
        this.clientId = this.generateClientId();
        this.currentConversationId = null;
        this.isConnected = false;
        this.settings = this.loadSettings();
        
        // Initialize application
        this.init();
    }
    
    init() {
        this.initializeElements();
        this.bindEvents();
        this.connectWebSocket();
        this.loadStatus();
        this.loadConversations();
        
        console.log('Intel AI Assistant initialized');
    }
    
    initializeElements() {
        // Core elements
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        // Header elements
        this.hardwareInfo = document.getElementById('hardwareInfo');
        this.settingsBtn = document.getElementById('settingsBtn');
        
        // Sidebar elements
        this.newChatBtn = document.getElementById('newChatBtn');
        this.conversationsList = document.getElementById('conversationsList');
        
        // Controls
        this.voiceToggle = document.getElementById('voiceToggle');
        this.clearChatBtn = document.getElementById('clearChatBtn');
        this.exportChatBtn = document.getElementById('exportChatBtn');
        
        // Settings modal
        this.settingsModal = document.getElementById('settingsModal');
        this.temperatureSlider = document.getElementById('temperatureSlider');
        this.maxTokensSlider = document.getElementById('maxTokensSlider');
        this.streamingToggle = document.getElementById('streamingToggle');
        
        // Quick actions
        this.quickActionBtns = document.querySelectorAll('.quick-btn');
        
        // Character count
        this.charCount = document.getElementById('charCount');
    }
    
    bindEvents() {
        // Message input
        this.messageInput.addEventListener('input', () => this.handleInputChange());
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Send button
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // New chat
        this.newChatBtn.addEventListener('click', () => this.startNewChat());
        
        // Clear chat
        this.clearChatBtn.addEventListener('click', () => this.clearCurrentChat());
        
        // Settings
        this.settingsBtn.addEventListener('click', () => this.openSettings());
        document.getElementById('closeSettingsBtn').addEventListener('click', () => this.closeSettings());
        document.getElementById('saveSettingsBtn').addEventListener('click', () => this.saveSettings());
        
        // Settings sliders
        this.temperatureSlider.addEventListener('input', (e) => {
            document.getElementById('temperatureValue').textContent = e.target.value;
        });
        
        this.maxTokensSlider.addEventListener('input', (e) => {
            document.getElementById('maxTokensValue').textContent = e.target.value;
        });
        
        // Quick actions
        this.quickActionBtns.forEach(btn => {
            btn.addEventListener('click', () => this.handleQuickAction(btn.dataset.action));
        });
        
        // Window events
        window.addEventListener('beforeunload', () => this.cleanup());
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResizeTextarea());
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/v1/chat/ws/${this.clientId}`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateStatus('ready', 'Connected');
                
                // Join current conversation if exists
                if (this.currentConversationId) {
                    this.joinConversation(this.currentConversationId);
                }
            };
            
            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateStatus('disconnected', 'Disconnected');
                
                // Attempt to reconnect after delay
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('error', 'Connection Error');
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateStatus('error', 'Failed to Connect');
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'response_chunk':
                this.handleResponseChunk(data);
                break;
                
            case 'response_complete':
                this.handleResponseComplete(data);
                break;
                
            case 'message_received':
                this.hideTypingIndicator();
                this.showTypingIndicator();
                break;
                
            case 'error':
                this.handleError(data.error);
                break;
                
            case 'pong':
                // Heartbeat response
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    sendMessage() {
        const content = this.messageInput.value.trim();
        if (!content || !this.isConnected) return;
        
        // Add user message to UI
        this.addMessage('user', content);
        
        // Clear input
        this.messageInput.value = '';
        this.handleInputChange();
        
        // Send via WebSocket
        const message = {
            type: 'message',
            content: content,
            conversation_id: this.currentConversationId,
            temperature: parseFloat(this.temperatureSlider.value),
            max_tokens: parseInt(this.maxTokensSlider.value)
        };
        
        this.websocket.send(JSON.stringify(message));
    }
    
    addMessage(role, content, options = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (options.isStreaming) {
            messageContent.innerHTML = '<span class="cursor">|</span>';
            messageDiv.dataset.streaming = 'true';
        } else {
            messageContent.textContent = content;
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        // Remove welcome message if present
        const welcomeMessage = this.messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageDiv;
    }
    
    handleResponseChunk(data) {
        let assistantMessage = this.messagesContainer.querySelector('.message.assistant[data-streaming="true"]');
        
        if (!assistantMessage) {
            assistantMessage = this.addMessage('assistant', '', { isStreaming: true });
        }
        
        const messageContent = assistantMessage.querySelector('.message-content');
        
        if (data.is_partial) {
            // Append chunk to existing content
            const currentText = messageContent.textContent.replace('|', '');
            messageContent.innerHTML = this.formatMessage(currentText + data.content) + '<span class="cursor">|</span>';
        }
        
        this.scrollToBottom();
    }
    
    handleResponseComplete(data) {
        const assistantMessage = this.messagesContainer.querySelector('.message.assistant[data-streaming="true"]');
        
        if (assistantMessage) {
            const messageContent = assistantMessage.querySelector('.message-content');
            const finalText = messageContent.textContent.replace('|', '');
            messageContent.innerHTML = this.formatMessage(finalText);
            
            assistantMessage.removeAttribute('data-streaming');
        }
        
        this.hideTypingIndicator();
        
        // Update conversation ID
        if (data.conversation_id) {
            this.currentConversationId = data.conversation_id;
        }
        
        // Show tool usage if any
        if (data.tools_used && data.tools_used.length > 0) {
            this.showToolUsage(data.tools_used);
        }
    }
    
    formatMessage(text) {
        // Basic markdown-like formatting
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        text = text.replace(/`(.*?)`/g, '<code>$1</code>');
        text = text.replace(/\n/g, '<br>');
        
        // Format URLs
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        return text;
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    showToolUsage(tools) {
        const toolsText = tools.join(', ');
        const toolMessage = document.createElement('div');
        toolMessage.className = 'tool-usage';
        toolMessage.innerHTML = `<i class="fas fa-tools"></i> Used tools: ${toolsText}`;
        this.messagesContainer.appendChild(toolMessage);
    }
    
    handleInputChange() {
        const content = this.messageInput.value;
        const charCount = content.length;
        
        // Update character count
        this.charCount.textContent = charCount;
        
        // Enable/disable send button
        this.sendBtn.disabled = !content.trim() || !this.isConnected;
        
        // Auto-resize
        this.autoResizeTextarea();
    }
    
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }
    
    handleQuickAction(action) {
        const actions = {
            'web-search': 'Search the web for ',
            'check-email': 'Check my recent emails'
        };
        
        if (actions[action]) {
            this.messageInput.value = actions[action];
            this.messageInput.focus();
            if (action === 'web-search') {
                // Position cursor after "Search the web for "
                this.messageInput.setSelectionRange(actions[action].length, actions[action].length);
            }
            this.handleInputChange();
        }
    }
    
    scrollToBottom() {
        requestAnimationFrame(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        });
    }
    
    startNewChat() {
        this.currentConversationId = null;
        this.messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">
                    <i class="fas fa-robot"></i>
                </div>
                <h3>New Conversation</h3>
                <p>Start a new conversation with your Intel AI Assistant!</p>
            </div>
        `;
        this.loadConversations(); // Refresh sidebar
    }
    
    clearCurrentChat() {
        if (this.currentConversationId) {
            if (confirm('Are you sure you want to clear this conversation?')) {
                fetch(`/api/v1/chat/conversations/${this.currentConversationId}/clear`, {
                    method: 'POST'
                })
                .then(() => this.startNewChat())
                .catch(error => console.error('Failed to clear chat:', error));
            }
        } else {
            this.startNewChat();
        }
    }
    
    joinConversation(conversationId) {
        if (this.websocket && this.isConnected) {
            const message = {
                type: 'join_conversation',
                conversation_id: conversationId
            };
            this.websocket.send(JSON.stringify(message));
        }
    }
    
    loadStatus() {
        fetch('/api/v1/chat/status')
            .then(response => response.json())
            .then(data => {
                this.updateStatus(data.status, `${data.agent_name} v${data.version}`);
                
                // Update hardware info
                if (data.capabilities && data.capabilities.hardware_requirements) {
                    const hw = data.capabilities.hardware_requirements;
                    document.getElementById('hardwareText').textContent = 
                        `Intel Core Ultra 7 (${hw.intel_optimization ? 'Optimized' : 'Standard'})`;
                }
                
                // Update tools list
                this.updateToolsList(data.available_tools || []);
            })
            .catch(error => {
                console.error('Failed to load status:', error);
                this.updateStatus('error', 'Status Unknown');
            });
    }
    
    updateStatus(status, text) {
        const statusDot = this.statusIndicator.querySelector('.status-dot');
        const statusText = this.statusIndicator.querySelector('.status-text');
        
        // Update status dot color
        const colors = {
            'ready': 'var(--success)',
            'initializing': 'var(--warning)', 
            'disconnected': 'var(--text-muted)',
            'error': 'var(--error)'
        };
        
        statusDot.style.background = colors[status] || colors.error;
        statusText.textContent = text;
    }
    
    updateToolsList(tools) {
        const toolsList = document.getElementById('toolsList');
        toolsList.innerHTML = '';
        
        tools.forEach(tool => {
            const toolItem = document.createElement('div');
            toolItem.className = 'tool-item';
            toolItem.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <span>${this.formatToolName(tool)}</span>
            `;
            toolsList.appendChild(toolItem);
        });
    }
    
    formatToolName(tool) {
        return tool.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    loadConversations() {
        fetch('/api/v1/chat/conversations')
            .then(response => response.json())
            .then(conversations => {
                this.updateConversationsList(conversations);
            })
            .catch(error => {
                console.error('Failed to load conversations:', error);
            });
    }
    
    updateConversationsList(conversations) {
        this.conversationsList.innerHTML = '';
        
        conversations.slice(0, 10).forEach(conv => {
            const convItem = document.createElement('div');
            convItem.className = 'conversation-item';
            convItem.innerHTML = `
                <div class="conversation-title">
                    Chat ${conv.conversation_id.slice(-8)}
                </div>
                <div class="conversation-meta">
                    ${conv.message_count} messages • ${this.formatDate(conv.last_activity)}
                </div>
            `;
            
            convItem.addEventListener('click', () => {
                this.loadConversation(conv.conversation_id);
            });
            
            this.conversationsList.appendChild(convItem);
        });
    }
    
    loadConversation(conversationId) {
        fetch(`/api/v1/chat/conversations/${conversationId}/history`)
            .then(response => response.json())
            .then(data => {
                this.currentConversationId = conversationId;
                this.messagesContainer.innerHTML = '';
                
                data.messages.forEach(msg => {
                    this.addMessage(msg.role, msg.content);
                });
                
                this.joinConversation(conversationId);
            })
            .catch(error => {
                console.error('Failed to load conversation:', error);
            });
    }
    
    openSettings() {
        // Load current settings
        this.temperatureSlider.value = this.settings.temperature;
        this.maxTokensSlider.value = this.settings.maxTokens;
        this.streamingToggle.checked = this.settings.streaming;
        
        document.getElementById('temperatureValue').textContent = this.settings.temperature;
        document.getElementById('maxTokensValue').textContent = this.settings.maxTokens;
        
        this.settingsModal.style.display = 'flex';
    }
    
    closeSettings() {
        this.settingsModal.style.display = 'none';
    }
    
    saveSettings() {
        this.settings = {
            temperature: parseFloat(this.temperatureSlider.value),
            maxTokens: parseInt(this.maxTokensSlider.value),
            streaming: this.streamingToggle.checked,
            sounds: document.getElementById('soundsToggle').checked,
            autoSave: document.getElementById('autoSaveToggle').checked
        };
        
        localStorage.setItem('intel-ai-settings', JSON.stringify(this.settings));
        this.closeSettings();
        
        this.showNotification('Settings saved successfully', 'success');
    }
    
    loadSettings() {
        const defaultSettings = {
            temperature: 0.7,
            maxTokens: 256,
            streaming: true,
            sounds: true,
            autoSave: true
        };
        
        try {
            const saved = localStorage.getItem('intel-ai-settings');
            return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
        } catch {
            return defaultSettings;
        }
    }
    
    showNotification(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.getElementById('toastContainer').appendChild(toast);
        
        setTimeout(() => toast.remove(), 3000);
    }
    
    handleError(error) {
        console.error('AI Assistant Error:', error);
        this.showNotification(`Error: ${error}`, 'error');
        this.hideTypingIndicator();
    }
    
    formatDate(dateStr) {
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return date.toLocaleDateString();
    }
    
    generateClientId() {
        return 'client_' + Math.random().toString(36).substring(2, 15);
    }
    
    cleanup() {
        if (this.websocket) {
            this.websocket.close();
        }
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aiAssistant = new IntelAIAssistant();
});