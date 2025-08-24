/**
 * Voice Handler for Speech Recognition and Text-to-Speech
 * Integrates with Intel Virtual Assistant voice APIs
 */

class VoiceHandler {
    constructor(app) {
        this.app = app;
        this.isRecording = false;
        this.isSpeaking = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.speechRecognition = null;
        
        this.init();
    }
    
    init() {
        // Initialize Web Speech API if available
        this.initSpeechRecognition();
        
        // Initialize Web Audio API for recording
        this.initAudioRecording();
        
        console.log('🎤 Voice handler initialized');
    }
    
    initSpeechRecognition() {
        // Check for Speech Recognition API support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            this.speechRecognition = new SpeechRecognition();
            this.speechRecognition.continuous = false;
            this.speechRecognition.interimResults = false;
            this.speechRecognition.lang = 'en-US';
            
            this.speechRecognition.onstart = () => {
                console.log('Speech recognition started');
                this.onRecordingStart();
            };
            
            this.speechRecognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                console.log('Speech recognized:', transcript);
                this.onTranscriptionComplete(transcript);
            };
            
            this.speechRecognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.onRecordingError(event.error);
            };
            
            this.speechRecognition.onend = () => {
                console.log('Speech recognition ended');
                this.onRecordingStop();
            };
        } else {
            console.warn('Speech Recognition API not supported');
        }
    }
    
    async initAudioRecording() {
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Create MediaRecorder for high-quality recording
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecordedAudio();
            };
            
            // Stop the stream initially
            stream.getTracks().forEach(track => track.stop());
            
            console.log('🎵 Audio recording initialized');
            
        } catch (error) {
            console.error('Failed to initialize audio recording:', error);
            this.app.showError('Microphone access denied or not available');
        }
    }
    
    async startRecording() {
        if (this.isRecording) return;
        
        try {
            // Use Web Speech API for real-time recognition if available
            if (this.speechRecognition) {
                this.speechRecognition.start();
                return;
            }
            
            // Fallback to manual recording
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecordedAudio();
                stream.getTracks().forEach(track => track.stop());
            };
            
            this.mediaRecorder.start();
            this.onRecordingStart();
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            this.app.showError('Failed to start voice recording');
        }
    }
    
    stopRecording() {
        if (!this.isRecording) return;
        
        if (this.speechRecognition) {
            this.speechRecognition.stop();
        } else if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
    }
    
    onRecordingStart() {
        this.isRecording = true;
        this.app.state.isRecording = true;
        
        // Update UI
        const voiceBtn = this.app.elements.voiceBtn;
        const voiceRecording = this.app.elements.voiceRecording;
        
        if (voiceBtn) {
            voiceBtn.textContent = '⏹️';
            voiceBtn.style.background = 'var(--danger-color)';
        }
        
        if (voiceRecording) {
            voiceRecording.style.display = 'flex';
        }
        
        this.app.showToast('Recording... Click microphone to stop');
    }
    
    onRecordingStop() {
        this.isRecording = false;
        this.app.state.isRecording = false;
        
        // Update UI
        const voiceBtn = this.app.elements.voiceBtn;
        const voiceRecording = this.app.elements.voiceRecording;
        
        if (voiceBtn) {
            voiceBtn.textContent = '🎤';
            voiceBtn.style.background = '';
        }
        
        if (voiceRecording) {
            voiceRecording.style.display = 'none';
        }
    }
    
    onRecordingError(error) {
        this.onRecordingStop();
        console.error('Recording error:', error);
        
        let errorMessage = 'Voice recording failed';
        switch (error) {
            case 'not-allowed':
                errorMessage = 'Microphone access denied';
                break;
            case 'no-speech':
                errorMessage = 'No speech detected';
                break;
            case 'audio-capture':
                errorMessage = 'Audio capture failed';
                break;
            case 'network':
                errorMessage = 'Network error during recording';
                break;
        }
        
        this.app.showError(errorMessage);
    }
    
    onTranscriptionComplete(transcript) {
        this.onRecordingStop();
        
        if (transcript.trim()) {
            // Insert transcript into message input
            if (this.app.elements.messageInput) {
                this.app.elements.messageInput.value = transcript;
                this.app.handleInputChange();
                this.app.autoResizeTextarea();
            }
            
            // Auto-send if voice mode is enabled
            if (this.app.state.isVoiceMode) {
                setTimeout(() => {
                    this.app.sendMessage();
                }, 500);
            }
        }
    }
    
    async processRecordedAudio() {
        if (this.audioChunks.length === 0) {
            this.onRecordingStop();
            return;
        }
        
        try {
            // Create audio blob
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            
            // Send to STT API
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('user_id', 'user');
            formData.append('language', 'auto');
            formData.append('provider', 'whisper');
            
            this.app.showToast('Processing speech...');
            
            const response = await fetch(`${this.app.config.apiBase}/voice/stt`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.transcript) {
                    this.onTranscriptionComplete(result.transcript);
                } else {
                    throw new Error(result.error_message || 'Transcription failed');
                }
            } else {
                throw new Error(`STT API error: ${response.status}`);
            }
            
        } catch (error) {
            console.error('Failed to process recorded audio:', error);
            this.app.showError('Speech processing failed');
        } finally {
            this.onRecordingStop();
            this.audioChunks = [];
        }
    }
    
    async speak(text) {
        if (this.isSpeaking || !this.app.config.voiceEnabled) return;
        
        try {
            this.isSpeaking = true;
            
            // Try Web Speech API first (faster)
            if ('speechSynthesis' in window) {
                await this.speakWithWebAPI(text);
            } else {
                // Fallback to server TTS
                await this.speakWithServerAPI(text);
            }
            
        } catch (error) {
            console.error('Text-to-speech failed:', error);
            // Try fallback method
            try {
                if ('speechSynthesis' in window) {
                    await this.speakWithWebAPI(text);
                }
            } catch (fallbackError) {
                console.error('Fallback TTS also failed:', fallbackError);
            }
        } finally {
            this.isSpeaking = false;
        }
    }
    
    async speakWithWebAPI(text) {
        return new Promise((resolve, reject) => {
            if (!('speechSynthesis' in window)) {
                reject(new Error('Speech synthesis not supported'));
                return;
            }
            
            const utterance = new SpeechSynthesisUtterance(text);
            
            // Configure voice
            const voices = speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice => 
                voice.name.includes('female') || voice.name.includes('Female')
            ) || voices[0];
            
            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }
            
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            utterance.onend = () => resolve();
            utterance.onerror = (error) => reject(error);
            
            speechSynthesis.speak(utterance);
        });
    }
    
    async speakWithServerAPI(text) {
        try {
            const response = await fetch(`${this.app.config.apiBase}/voice/tts/simple?text=${encodeURIComponent(text)}&voice_id=${this.app.config.voice}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const audioBlob = await response.blob();
                await this.playAudioBlob(audioBlob);
            } else {
                throw new Error(`TTS API error: ${response.status}`);
            }
            
        } catch (error) {
            console.error('Server TTS failed:', error);
            throw error;
        }
    }
    
    async playAudioBlob(audioBlob) {
        return new Promise((resolve, reject) => {
            const audio = new Audio();
            const audioUrl = URL.createObjectURL(audioBlob);
            
            audio.src = audioUrl;
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                resolve();
            };
            audio.onerror = (error) => {
                URL.revokeObjectURL(audioUrl);
                reject(error);
            };
            
            audio.play().catch(reject);
        });
    }
    
    stopSpeaking() {
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
        this.isSpeaking = false;
    }
    
    // Voice input toggle handler
    toggleVoiceInput() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }
    
    // Get available voices for settings
    getAvailableVoices() {
        if ('speechSynthesis' in window) {
            return speechSynthesis.getVoices().map(voice => ({
                id: voice.name,
                name: voice.name,
                language: voice.lang,
                gender: this.guessVoiceGender(voice.name)
            }));
        }
        return [];
    }
    
    guessVoiceGender(voiceName) {
        const name = voiceName.toLowerCase();
        if (name.includes('female') || name.includes('woman') || name.includes('girl')) {
            return 'female';
        } else if (name.includes('male') || name.includes('man') || name.includes('boy')) {
            return 'male';
        }
        return 'neutral';
    }
    
    // Cleanup method
    destroy() {
        this.stopRecording();
        this.stopSpeaking();
        
        if (this.mediaRecorder && this.mediaRecorder.stream) {
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }
}

// Export for use in main app
window.VoiceHandler = VoiceHandler;