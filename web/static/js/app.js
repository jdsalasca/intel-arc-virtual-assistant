/**
 * Intel Virtual Assistant - Main Application
 * Handles app initialization, state management, and core functionality
 */

class VirtualAssistant {
    constructor() {
        this.config = {
            apiBase: '/api/v1',
            model: 'qwen2.5-7b-int4',
            voice: 'female_1',
            temperature: 0.7,
            maxTokens: 256,
            voiceEnabled: true,
            autoScroll: true
        };
        
        this.state = {
            currentConversationId: null,
            conversations: [],
            isConnected: false,
            isVoiceMode: false,
            isRecording: false,
            hardwareStatus: {
                gpu: 'checking',
                npu: 'checking',
                model: 'loading'
            }
        };
        
        this.elements = {};
        this.eventListeners = [];
        
        this.init();
    }
    
    async init() {
        try {
            console.log('🚀 Initializing Intel Virtual Assistant...');
            
            // Initialize DOM elements
            this.initElements();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Load user settings
            this.loadSettings();
            
            // Check server connection
            await this.checkConnection();
            
            // Load hardware status
            await this.loadHardwareStatus();
            
            // Load conversations
            await this.loadConversations();
            
            // Initialize voice functionality
            if (window.VoiceHandler) {
                this.voiceHandler = new VoiceHandler(this);
            }
            
            console.log('✅ Virtual Assistant initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize Virtual Assistant:', error);
            this.showError('Failed to initialize application');
        }
    }
    
    initElements() {
        // Cache frequently used DOM elements
        this.elements = {
            // Header elements
            themeToggle: document.getElementById('theme-toggle'),
            settingsBtn: document.getElementById('settings-btn'),
            connectionStatus: document.getElementById('connection-status'),
            
            // Sidebar elements
            newChatBtn: document.getElementById('new-chat-btn'),
            conversationList: document.getElementById('conversation-list'),
            
            // Hardware status
            gpuStatus: document.getElementById('gpu-status'),
            npuStatus: document.getElementById('npu-status'),
            activeModel: document.getElementById('active-model'),
            
            // Chat elements
            chatTitle: document.getElementById('chat-title'),
            chatMessages: document.getElementById('chat-messages'),
            messageInput: document.getElementById('message-input'),
            sendBtn: document.getElementById('send-btn'),
            voiceBtn: document.getElementById('voice-btn'),
            attachBtn: document.getElementById('attach-btn'),
            
            // Voice elements
            voiceToggle: document.getElementById('voice-toggle'),
            voiceRecording: document.getElementById('voice-recording'),
            
            // Model status
            modelInfo: document.getElementById('model-info'),
            typingIndicator: document.getElementById('typing-indicator'),
            
            // Settings modal
            settingsModal: document.getElementById('settings-modal'),
            settingsClose: document.getElementById('settings-close'),
            modelSelect: document.getElementById('model-select'),
            voiceSelect: document.getElementById('voice-select'),
            temperatureSlider: document.getElementById('temperature-slider'),
            temperatureValue: document.getElementById('temperature-value'),
            maxTokensSlider: document.getElementById('max-tokens-slider'),
            maxTokensValue: document.getElementById('max-tokens-value'),
            voiceEnabledCheck: document.getElementById('voice-enabled'),
            autoScrollCheck: document.getElementById('auto-scroll'),
            settingsCancel: document.getElementById('settings-cancel'),
            settingsSave: document.getElementById('settings-save')
        };
    }
    
    setupEventListeners() {
        // Theme toggle
        this.elements.themeToggle?.addEventListener('click', () => this.toggleTheme());
        
        // Settings
        this.elements.settingsBtn?.addEventListener('click', () => this.openSettings());
        this.elements.settingsClose?.addEventListener('click', () => this.closeSettings());
        this.elements.settingsCancel?.addEventListener('click', () => this.closeSettings());
        this.elements.settingsSave?.addEventListener('click', () => this.saveSettings());
        
        // New chat
        this.elements.newChatBtn?.addEventListener('click', () => this.createNewChat());
        
        // Message input
        this.elements.messageInput?.addEventListener('input', () => this.handleInputChange());
        this.elements.messageInput?.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Send button
        this.elements.sendBtn?.addEventListener('click', () => this.sendMessage());
        
        // Voice button
        this.elements.voiceBtn?.addEventListener('click', () => this.toggleVoiceInput());
        this.elements.voiceToggle?.addEventListener('click', () => this.toggleVoiceMode());
        
        // Settings sliders
        this.elements.temperatureSlider?.addEventListener('input', (e) => {
            this.elements.temperatureValue.textContent = e.target.value;
        });
        
        this.elements.maxTokensSlider?.addEventListener('input', (e) => {
            this.elements.maxTokensValue.textContent = e.target.value;
        });
        
        // Click outside modal to close
        this.elements.settingsModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.settingsModal) {
                this.closeSettings();
            }
        });
        
        // Auto-resize textarea
        if (this.elements.messageInput) {
            this.elements.messageInput.addEventListener('input', this.autoResizeTextarea.bind(this));
        }
    }
    
    async checkConnection() {
        try {
            const response = await fetch(`${this.config.apiBase}/health/status`);
            if (response.ok) {
                this.state.isConnected = true;
                this.updateConnectionStatus('Connected', 'online');
            } else {
                throw new Error('Server responded with error');
            }
        } catch (error) {
            this.state.isConnected = false;
            this.updateConnectionStatus('Disconnected', 'offline');
            console.error('Connection check failed:', error);
        }
    }
    
    async loadHardwareStatus() {
        try {
            const response = await fetch(`${this.config.apiBase}/health/hardware`);
            if (response.ok) {
                const hardware = await response.json();
                
                // Update GPU status
                const gpuAvailable = hardware.arc_gpu?.available;
                this.updateHardwareStatus('gpu', gpuAvailable ? 'Available' : 'Not Available', 
                                        gpuAvailable ? 'online' : 'offline');
                
                // Update NPU status
                const npuAvailable = hardware.npu?.available;
                this.updateHardwareStatus('npu', npuAvailable ? 'Available' : 'Not Available',
                                        npuAvailable ? 'online' : 'offline');
                
                // Update active model
                this.updateHardwareStatus('model', this.config.model, 'online');
                
                this.state.hardwareStatus = {
                    gpu: gpuAvailable ? 'online' : 'offline',
                    npu: npuAvailable ? 'online' : 'offline',
                    model: 'online'
                };
            }
        } catch (error) {
            console.error('Failed to load hardware status:', error);
            this.updateHardwareStatus('gpu', 'Unknown', 'offline');
            this.updateHardwareStatus('npu', 'Unknown', 'offline');
            this.updateHardwareStatus('model', 'Error', 'offline');
        }
    }
    
    async loadConversations() {
        try {
            // For now, we'll create a mock conversation list
            // In a real implementation, this would fetch from the API
            this.state.conversations = [
                {
                    id: 'conv1',
                    title: 'Welcome Conversation',
                    preview: 'Getting started with the assistant...',
                    timestamp: new Date().toISOString()
                }
            ];
            
            this.renderConversations();
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    }
    
    renderConversations() {
        if (!this.elements.conversationList) return;
        
        const conversationsHtml = this.state.conversations.map(conv => `
            <div class="conversation-item ${conv.id === this.state.currentConversationId ? 'active' : ''}" 
                 onclick="app.selectConversation('${conv.id}')">
                <div class="conversation-title">${conv.title}</div>
                <div class="conversation-preview">${conv.preview}</div>
                <div class="conversation-time">${this.formatTime(conv.timestamp)}</div>
            </div>
        `).join('');
        
        this.elements.conversationList.innerHTML = conversationsHtml;
    }
    
    selectConversation(conversationId) {
        this.state.currentConversationId = conversationId;
        const conversation = this.state.conversations.find(c => c.id === conversationId);
        
        if (conversation) {
            this.elements.chatTitle.textContent = conversation.title;
            this.renderConversations(); // Re-render to update active state
            this.loadConversationMessages(conversationId);
        }
    }
    
    async loadConversationMessages(conversationId) {
        try {
            // Clear current messages
            this.clearMessages();
            
            // For now, show welcome message for new conversations
            if (conversationId === 'conv1') {
                // Welcome message is already in HTML
                return;
            }
            
            // In a real implementation, load messages from API
            // const response = await fetch(`${this.config.apiBase}/chat/conversations/${conversationId}/messages`);
            // const messages = await response.json();
            // this.renderMessages(messages);
            
        } catch (error) {
            console.error('Failed to load conversation messages:', error);
        }
    }
    
    createNewChat() {
        const newConversation = {
            id: `conv_${Date.now()}`,
            title: 'New Conversation',
            preview: 'Start a new conversation...',
            timestamp: new Date().toISOString()
        };
        
        this.state.conversations.unshift(newConversation);
        this.selectConversation(newConversation.id);
        this.clearMessages();
        
        // Focus on input
        this.elements.messageInput?.focus();
    }
    
    clearMessages() {
        if (this.elements.chatMessages) {
            this.elements.chatMessages.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">🤖</div>
                    <h3>New Conversation Started</h3>
                    <p>I'm ready to help! What would you like to discuss?</p>
                </div>
            `;
        }
    }
    
    handleInputChange() {
        const hasText = this.elements.messageInput?.value.trim().length > 0;
        if (this.elements.sendBtn) {
            this.elements.sendBtn.disabled = !hasText;
        }
    }
    
    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }
    
    async sendMessage() {
        const message = this.elements.messageInput?.value.trim();
        if (!message) return;
        
        try {
            // Clear input
            this.elements.messageInput.value = '';
            this.handleInputChange();
            this.autoResizeTextarea();
            
            // Add user message to chat
            this.addMessage('user', message);
            
            // Show typing indicator
            this.showTypingIndicator();
            
            // Send to API
            const response = await fetch(`${this.config.apiBase}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: this.config.model,
                    messages: [{ role: 'user', content: message }],
                    temperature: this.config.temperature,
                    max_tokens: this.config.maxTokens
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                const assistantMessage = data.choices?.[0]?.message?.content || 'Sorry, I could not generate a response.';
                
                // Add assistant message
                this.addMessage('assistant', assistantMessage);
                
                // Text-to-speech if enabled
                if (this.config.voiceEnabled && this.voiceHandler) {
                    this.voiceHandler.speak(assistantMessage);
                }
            } else {
                throw new Error(`API error: ${response.status}`);
            }
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        } finally {
            this.hideTypingIndicator();
        }
    }
    
    addMessage(role, content) {
        if (!this.elements.chatMessages) return;
        
        // Remove welcome message if it exists
        const welcomeMsg = this.elements.chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        const messageId = `msg_${Date.now()}`;
        const timestamp = new Date().toLocaleTimeString();
        const avatar = role === 'user' ? '👤' : '🤖';
        
        const messageHtml = `
            <div class="message ${role}" id="${messageId}">
                <div class="message-avatar">${avatar}</div>
                <div class="message-bubble">
                    <div class="message-content">
                        <p>${this.formatMessageContent(content)}</p>
                    </div>
                    <div class="message-meta">
                        <span class="message-time">${timestamp}</span>
                        <div class="message-actions">
                            <button class="message-action" onclick="app.copyMessage('${messageId}')" title="Copy">📋</button>
                            ${role === 'assistant' ? `<button class="message-action" onclick="app.speakMessage('${messageId}')" title="Speak">🔊</button>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.elements.chatMessages.insertAdjacentHTML('beforeend', messageHtml);
        
        // Auto-scroll if enabled
        if (this.config.autoScroll) {
            this.scrollToBottom();
        }
    }
    
    formatMessageContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    copyMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            const content = message.querySelector('.message-content p').textContent;
            navigator.clipboard.writeText(content).then(() => {
                this.showToast('Message copied to clipboard');
            });
        }
    }
    
    speakMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message && this.voiceHandler) {
            const content = message.querySelector('.message-content p').textContent;
            this.voiceHandler.speak(content);
        }
    }
    
    showTypingIndicator() {
        if (this.elements.typingIndicator) {
            this.elements.typingIndicator.style.display = 'flex';
        }
    }
    
    hideTypingIndicator() {
        if (this.elements.typingIndicator) {
            this.elements.typingIndicator.style.display = 'none';
        }
    }
    
    scrollToBottom() {
        if (this.elements.chatMessages) {
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        }
    }
    
    autoResizeTextarea() {
        const textarea = this.elements.messageInput;
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }
    }
    
    toggleTheme() {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        
        if (this.elements.themeToggle) {
            this.elements.themeToggle.textContent = isDark ? '☀️' : '🌙';
        }
        
        // Save theme preference
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }
    
    toggleVoiceMode() {
        this.state.isVoiceMode = !this.state.isVoiceMode;
        
        if (this.elements.voiceToggle) {
            this.elements.voiceToggle.classList.toggle('active', this.state.isVoiceMode);
        }
        
        this.showToast(this.state.isVoiceMode ? 'Voice mode enabled' : 'Voice mode disabled');
    }
    
    toggleVoiceInput() {
        if (this.voiceHandler) {
            if (this.state.isRecording) {
                this.voiceHandler.stopRecording();
            } else {
                this.voiceHandler.startRecording();
            }
        }
    }
    
    updateConnectionStatus(text, status) {
        if (this.elements.connectionStatus) {
            const statusText = this.elements.connectionStatus.querySelector('.status-text');
            const statusDot = this.elements.connectionStatus.querySelector('.status-dot');
            
            if (statusText) statusText.textContent = text;
            if (statusDot) {
                statusDot.className = `status-dot ${status}`;
            }
        }
    }
    
    updateHardwareStatus(type, text, status) {
        const element = this.elements[`${type}Status`];
        if (element) {
            element.textContent = text;
            element.className = `hw-status ${status}`;
        }
    }
    
    openSettings() {
        if (this.elements.settingsModal) {
            this.elements.settingsModal.classList.add('show');
            this.loadSettingsValues();
        }
    }
    
    closeSettings() {
        if (this.elements.settingsModal) {
            this.elements.settingsModal.classList.remove('show');
        }
    }
    
    loadSettingsValues() {
        if (this.elements.modelSelect) this.elements.modelSelect.value = this.config.model;
        if (this.elements.voiceSelect) this.elements.voiceSelect.value = this.config.voice;
        if (this.elements.temperatureSlider) {
            this.elements.temperatureSlider.value = this.config.temperature;
            this.elements.temperatureValue.textContent = this.config.temperature;
        }
        if (this.elements.maxTokensSlider) {
            this.elements.maxTokensSlider.value = this.config.maxTokens;
            this.elements.maxTokensValue.textContent = this.config.maxTokens;
        }
        if (this.elements.voiceEnabledCheck) this.elements.voiceEnabledCheck.checked = this.config.voiceEnabled;
        if (this.elements.autoScrollCheck) this.elements.autoScrollCheck.checked = this.config.autoScroll;
    }
    
    saveSettings() {
        // Update config from form values
        if (this.elements.modelSelect) this.config.model = this.elements.modelSelect.value;
        if (this.elements.voiceSelect) this.config.voice = this.elements.voiceSelect.value;
        if (this.elements.temperatureSlider) this.config.temperature = parseFloat(this.elements.temperatureSlider.value);
        if (this.elements.maxTokensSlider) this.config.maxTokens = parseInt(this.elements.maxTokensSlider.value);
        if (this.elements.voiceEnabledCheck) this.config.voiceEnabled = this.elements.voiceEnabledCheck.checked;
        if (this.elements.autoScrollCheck) this.config.autoScroll = this.elements.autoScrollCheck.checked;
        
        // Update model info display
        this.updateModelInfo();
        
        // Save to localStorage
        this.saveSettingsToStorage();
        
        this.closeSettings();
        this.showToast('Settings saved successfully');
    }
    
    updateModelInfo() {
        if (this.elements.modelInfo) {
            const deviceType = this.state.hardwareStatus.gpu === 'online' ? 'Arc GPU' : 'CPU';
            this.elements.modelInfo.textContent = `${this.config.model} (${deviceType})`;
        }
    }
    
    loadSettings() {
        try {
            const saved = localStorage.getItem('assistantSettings');
            if (saved) {
                const settings = JSON.parse(saved);
                Object.assign(this.config, settings);
            }
            
            // Load theme
            const theme = localStorage.getItem('theme') || 'dark';
            if (theme === 'light') {
                document.body.classList.remove('dark-theme');
                if (this.elements.themeToggle) this.elements.themeToggle.textContent = '🌙';
            }
            
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }
    
    saveSettingsToStorage() {
        try {
            localStorage.setItem('assistantSettings', JSON.stringify(this.config));
        } catch (error) {
            console.error('Failed to save settings:', error);
        }
    }
    
    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--accent-primary);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            box-shadow: var(--shadow);
            z-index: 2000;
            animation: slideInRight 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    showError(message) {
        this.showToast(message, 'error');
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return date.toLocaleDateString();
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VirtualAssistant();
});

// Add CSS animations for toasts
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);