/**
 * Utility Functions for Intel Virtual Assistant
 * Common helper functions and utilities
 */

// Utility namespace
window.Utils = {
    
    // Format file size in human readable format
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Format duration in human readable format
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    },
    
    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle function
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // Generate UUID
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    },
    
    // Escape HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    // Parse markdown-like text
    parseMarkdown(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/\n/g, '<br>');
    },
    
    // Copy to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                return true;
            } catch (err) {
                return false;
            } finally {
                document.body.removeChild(textArea);
            }
        }
    },
    
    // Download file
    downloadFile(content, filename, contentType = 'text/plain') {
        const a = document.createElement('a');
        const file = new Blob([content], { type: contentType });
        a.href = URL.createObjectURL(file);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);
    },
    
    // Check if device is mobile
    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    // Check if browser supports feature
    supportsFeature(feature) {
        const features = {
            webrtc: () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
            speechRecognition: () => !!(window.SpeechRecognition || window.webkitSpeechRecognition),
            speechSynthesis: () => !!window.speechSynthesis,
            notifications: () => !!window.Notification,
            serviceWorker: () => !!navigator.serviceWorker,
            webWorker: () => !!window.Worker,
            indexedDB: () => !!window.indexedDB,
            localStorage: () => {
                try {
                    const test = 'test';
                    localStorage.setItem(test, test);
                    localStorage.removeItem(test);
                    return true;
                } catch(e) {
                    return false;
                }
            }
        };
        
        return features[feature] ? features[feature]() : false;
    },
    
    // Format relative time
    formatRelativeTime(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
        if (diffInSeconds < 2419200) return `${Math.floor(diffInSeconds / 604800)}w ago`;
        
        return date.toLocaleDateString();
    },
    
    // Validate email
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },
    
    // Validate URL
    isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    },
    
    // Get file extension
    getFileExtension(filename) {
        return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
    },
    
    // Check file type
    getFileType(filename) {
        const ext = this.getFileExtension(filename).toLowerCase();
        
        const types = {
            image: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'],
            audio: ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'],
            video: ['mp4', 'webm', 'avi', 'mov', 'wmv', 'flv'],
            document: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf'],
            archive: ['zip', 'rar', '7z', 'tar', 'gz'],
            code: ['js', 'html', 'css', 'py', 'java', 'cpp', 'c', 'php', 'rb', 'go']
        };
        
        for (const [type, extensions] of Object.entries(types)) {
            if (extensions.includes(ext)) {
                return type;
            }
        }
        
        return 'unknown';
    },
    
    // Animate element
    animate(element, animation, duration = 300) {
        return new Promise(resolve => {
            element.style.animation = `${animation} ${duration}ms ease`;
            element.addEventListener('animationend', function handler() {
                element.removeEventListener('animationend', handler);
                element.style.animation = '';
                resolve();
            });
        });
    },
    
    // Smooth scroll to element
    scrollToElement(element, offset = 0) {
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    },
    
    // Create loading spinner
    createLoadingSpinner(size = 'medium') {
        const spinner = document.createElement('div');
        spinner.className = `loading-spinner loading-spinner-${size}`;
        spinner.innerHTML = '<div></div><div></div><div></div><div></div>';
        return spinner;
    },
    
    // Show confirmation dialog
    confirm(message, title = 'Confirm') {
        return new Promise(resolve => {
            const modal = document.createElement('div');
            modal.className = 'confirm-modal';
            modal.innerHTML = `
                <div class="confirm-content">
                    <h3>${title}</h3>
                    <p>${message}</p>
                    <div class="confirm-actions">
                        <button class="btn btn-secondary confirm-cancel">Cancel</button>
                        <button class="btn btn-primary confirm-ok">OK</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            const cleanup = () => {
                document.body.removeChild(modal);
            };
            
            modal.querySelector('.confirm-cancel').onclick = () => {
                cleanup();
                resolve(false);
            };
            
            modal.querySelector('.confirm-ok').onclick = () => {
                cleanup();
                resolve(true);
            };
            
            modal.onclick = (e) => {
                if (e.target === modal) {
                    cleanup();
                    resolve(false);
                }
            };
        });
    },
    
    // Create progress bar
    createProgressBar(container, initialProgress = 0) {
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        progressBar.innerHTML = `
            <div class="progress-fill" style="width: ${initialProgress}%"></div>
            <div class="progress-text">${initialProgress}%</div>
        `;
        
        container.appendChild(progressBar);
        
        return {
            update(progress) {
                const fill = progressBar.querySelector('.progress-fill');
                const text = progressBar.querySelector('.progress-text');
                fill.style.width = `${progress}%`;
                text.textContent = `${progress}%`;
            },
            remove() {
                if (progressBar.parentNode) {
                    progressBar.parentNode.removeChild(progressBar);
                }
            }
        };
    },
    
    // Local storage with expiration
    storage: {
        set(key, value, expirationHours = 24) {
            const item = {
                value: value,
                expiration: Date.now() + (expirationHours * 60 * 60 * 1000)
            };
            localStorage.setItem(key, JSON.stringify(item));
        },
        
        get(key) {
            const itemStr = localStorage.getItem(key);
            if (!itemStr) return null;
            
            try {
                const item = JSON.parse(itemStr);
                if (Date.now() > item.expiration) {
                    localStorage.removeItem(key);
                    return null;
                }
                return item.value;
            } catch (e) {
                localStorage.removeItem(key);
                return null;
            }
        },
        
        remove(key) {
            localStorage.removeItem(key);
        },
        
        clear() {
            localStorage.clear();
        }
    }
};

// Add CSS for utility components
const utilityStyles = `
    .loading-spinner {
        display: inline-block;
        position: relative;
    }
    
    .loading-spinner div {
        box-sizing: border-box;
        display: block;
        position: absolute;
        border: 2px solid var(--accent-primary);
        border-radius: 50%;
        animation: loading-spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
        border-color: var(--accent-primary) transparent transparent transparent;
    }
    
    .loading-spinner-small {
        width: 20px;
        height: 20px;
    }
    
    .loading-spinner-small div {
        width: 16px;
        height: 16px;
        margin: 2px;
    }
    
    .loading-spinner-medium {
        width: 40px;
        height: 40px;
    }
    
    .loading-spinner-medium div {
        width: 32px;
        height: 32px;
        margin: 4px;
    }
    
    .loading-spinner-large {
        width: 80px;
        height: 80px;
    }
    
    .loading-spinner-large div {
        width: 64px;
        height: 64px;
        margin: 8px;
    }
    
    .loading-spinner div:nth-child(1) { animation-delay: -0.45s; }
    .loading-spinner div:nth-child(2) { animation-delay: -0.3s; }
    .loading-spinner div:nth-child(3) { animation-delay: -0.15s; }
    
    @keyframes loading-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .confirm-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
    }
    
    .confirm-content {
        background: var(--bg-primary);
        border-radius: 1rem;
        padding: 2rem;
        max-width: 400px;
        width: 90%;
        box-shadow: var(--shadow-hover);
    }
    
    .confirm-content h3 {
        margin-bottom: 1rem;
        color: var(--text-primary);
    }
    
    .confirm-content p {
        margin-bottom: 2rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    .confirm-actions {
        display: flex;
        gap: 1rem;
        justify-content: flex-end;
    }
    
    .progress-bar {
        width: 100%;
        height: 20px;
        background: var(--bg-tertiary);
        border-radius: 10px;
        position: relative;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        background: var(--accent-primary);
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    
    .progress-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-primary);
    }
`;

// Add styles to document
const styleSheet = document.createElement('style');
styleSheet.textContent = utilityStyles;
document.head.appendChild(styleSheet);