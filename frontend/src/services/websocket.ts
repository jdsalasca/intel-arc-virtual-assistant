import { io, Socket } from 'socket.io-client';
import { WebSocketMessage, ChatMessage } from '@types/index';

export class WebSocketService {
  private socket: Socket | null = null;
  private url: string;
  private clientId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private listeners: Map<string, ((data: any) => void)[]> = new Map();

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.url = baseUrl;
    this.clientId = this.generateClientId();
  }

  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        resolve();
        return;
      }

      try {
        // Convert HTTP URL to WebSocket URL
        const wsUrl = this.url.replace(/^https?/, this.url.startsWith('https') ? 'wss' : 'ws');
        const fullWsUrl = `${wsUrl}/api/v1/chat/ws/${this.clientId}`;

        // Create native WebSocket connection
        const ws = new WebSocket(fullWsUrl);

        ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.setupHeartbeat(ws);
          resolve();
        };

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.handleDisconnection();
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        // Store as socket-like object
        this.socket = {
          connected: false,
          emit: (event: string, data: any) => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: event, ...data }));
            }
          },
          disconnect: () => ws.close(),
        } as Socket;

        // Update connection status when open
        ws.onopen = () => {
          if (this.socket) {
            (this.socket as any).connected = true;
          }
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.setupHeartbeat(ws);
          resolve();
        };

      } catch (error) {
        console.error('WebSocket connection failed:', error);
        reject(error);
      }
    });
  }

  private setupHeartbeat(ws: WebSocket) {
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }));
      } else {
        clearInterval(pingInterval);
      }
    }, 30000); // Ping every 30 seconds
  }

  private handleMessage(message: WebSocketMessage) {
    console.log('WebSocket message received:', message);
    
    switch (message.type) {
      case 'message':
        this.emit('message', message);
        break;
      case 'joined_conversation':
        this.emit('joined_conversation', message);
        break;
      case 'pong':
        // Heartbeat response - no action needed
        break;
      case 'error':
        console.error('WebSocket error message:', message.error);
        this.emit('error', message);
        break;
      default:
        console.warn('Unknown WebSocket message type:', message.type);
    }
  }

  private handleDisconnection() {
    if (this.socket) {
      (this.socket as any).connected = false;
    }
    
    this.emit('disconnect');
    
    // Auto-reconnect logic
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error);
        });
      }, this.reconnectInterval * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
      this.emit('max_reconnect_attempts');
    }
  }

  sendMessage(content: string, conversationId?: string) {
    if (!this.socket?.connected) {
      throw new Error('WebSocket not connected');
    }

    this.socket.emit('message', {
      content,
      conversation_id: conversationId,
      timestamp: new Date().toISOString(),
    });
  }

  joinConversation(conversationId: string) {
    if (!this.socket?.connected) {
      throw new Error('WebSocket not connected');
    }

    this.socket.emit('join_conversation', {
      conversation_id: conversationId,
    });
  }

  // Event listener management
  on(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  off(event: string, callback?: (data: any) => void) {
    const eventListeners = this.listeners.get(event);
    if (!eventListeners) return;

    if (callback) {
      const index = eventListeners.indexOf(callback);
      if (index > -1) {
        eventListeners.splice(index, 1);
      }
    } else {
      this.listeners.set(event, []);
    }
  }

  private emit(event: string, data?: any) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(callback => callback(data));
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.listeners.clear();
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getClientId(): string {
    return this.clientId;
  }
}

// Create and export singleton instance
let wsServiceInstance: WebSocketService | null = null;

export const getWebSocketService = (baseUrl?: string): WebSocketService => {
  if (!wsServiceInstance) {
    wsServiceInstance = new WebSocketService(baseUrl);
  }
  return wsServiceInstance;
};

export default WebSocketService;