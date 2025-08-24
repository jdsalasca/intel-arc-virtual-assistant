import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  ApiResponse, 
  ChatRequest, 
  ChatResponse, 
  SystemHealth, 
  ModelInfo,
  ToolInfo,
  VoiceRequest,
  VoiceResponse,
  Conversation 
} from '@types/index';

class ApiService {
  private api: AxiosInstance;
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    this.api = axios.create({
      baseURL: this.baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health and system endpoints
  async getHealth(): Promise<SystemHealth> {
    const response = await this.api.get<SystemHealth>('/api/v1/health/status');
    return response.data;
  }

  async getHardwareInfo(): Promise<any> {
    const response = await this.api.get('/api/v1/health/hardware');
    return response.data;
  }

  // Model endpoints
  async getModels(): Promise<ModelInfo[]> {
    const response = await this.api.get<{ data: ModelInfo[] }>('/api/v1/models');
    return response.data.data;
  }

  async getActiveModel(): Promise<ModelInfo | null> {
    try {
      const models = await this.getModels();
      return models.find(model => model.loaded) || null;
    } catch (error) {
      console.error('Failed to get active model:', error);
      return null;
    }
  }

  // Tool endpoints
  async getTools(): Promise<ToolInfo[]> {
    const response = await this.api.get<ToolInfo[]>('/api/v1/tools/available');
    return response.data;
  }

  // Chat endpoints
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.api.post<ChatResponse>('/api/v1/chat/message', request);
    return response.data;
  }

  async getConversations(): Promise<Conversation[]> {
    const response = await this.api.get<Conversation[]>('/api/v1/chat/conversations');
    return response.data;
  }

  async getConversation(id: string): Promise<Conversation> {
    const response = await this.api.get<Conversation>(`/api/v1/chat/conversations/${id}`);
    return response.data;
  }

  async createConversation(title?: string): Promise<Conversation> {
    const response = await this.api.post<Conversation>('/api/v1/chat/conversations', {
      title: title || 'New Conversation'
    });
    return response.data;
  }

  async deleteConversation(id: string): Promise<void> {
    await this.api.delete(`/api/v1/chat/conversations/${id}`);
  }

  async clearConversation(id: string): Promise<void> {
    await this.api.post(`/api/v1/chat/conversations/${id}/clear`);
  }

  // Voice endpoints
  async synthesizeSpeech(request: VoiceRequest): Promise<VoiceResponse> {
    const response = await this.api.post<VoiceResponse>('/api/v1/voice/tts', request);
    return response.data;
  }

  async getVoiceStatus(): Promise<any> {
    const response = await this.api.get('/api/v1/voice/status');
    return response.data;
  }

  // WebSocket connection
  getWebSocketUrl(clientId: string): string {
    const wsProtocol = this.baseUrl.startsWith('https') ? 'wss' : 'ws';
    const wsUrl = this.baseUrl.replace(/^https?/, wsProtocol);
    return `${wsUrl}/api/v1/chat/ws/${clientId}`;
  }

  // File upload (if needed)
  async uploadFile(file: File, conversationId?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }

    const response = await this.api.post('/api/v1/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Streaming response helper
  async streamMessage(
    request: ChatRequest,
    onData: (data: string) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ ...request, stream: true }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data.trim() === '[DONE]') {
                onComplete?.();
                return;
              }
              try {
                const parsed = JSON.parse(data);
                if (parsed.content) {
                  onData(parsed.content);
                }
                if (parsed.is_final) {
                  onComplete?.();
                  return;
                }
              } catch (e) {
                console.warn('Failed to parse streaming data:', data);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('Streaming error:', error);
      onError?.(error as Error);
    }
  }
}

// Create and export singleton instance
export const apiService = new ApiService();
export default apiService;