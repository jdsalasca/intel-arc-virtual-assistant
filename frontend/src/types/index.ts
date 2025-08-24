// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Chat types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  conversation_id?: string;
  tools_used?: string[];
  processing_time?: number;
  is_partial?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  last_activity: string;
  message_count: number;
  messages?: ChatMessage[];
}

export interface ChatRequest {
  content: string;
  conversation_id?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface ChatResponse {
  content: string;
  conversation_id: string;
  success: boolean;
  error?: string;
  tools_used?: string[];
  processing_time?: number;
  timestamp: string;
}

// Voice types
export interface VoiceRequest {
  text: string;
  voice?: string;
  speed?: number;
  pitch?: number;
}

export interface VoiceResponse {
  audio_url: string;
  duration?: number;
  format: string;
}

export interface SpeechRecognitionResult {
  text: string;
  confidence: number;
  is_final: boolean;
}

// Hardware and system types
export interface HardwareStatus {
  cpu: {
    available: boolean;
    model?: string;
    usage?: number;
  };
  arc_gpu: {
    available: boolean;
    model?: string;
    memory?: number;
    usage?: number;
  };
  npu: {
    available: boolean;
    model?: string;
    performance?: string;
  };
}

export interface SystemHealth {
  status: 'ok' | 'warning' | 'error' | 'initializing';
  loaded_models: string[];
  hardware: HardwareStatus;
  uptime?: number;
  memory_usage?: number;
}

// Model types
export interface ModelInfo {
  id: string;
  object: string;
  owned_by: string;
  loaded: boolean;
  size?: number;
  description?: string;
}

// Tool types
export interface ToolInfo {
  id: string;
  name: string;
  description: string;
  available: boolean;
  parameters?: Record<string, any>;
}

// Settings types
export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  model: string;
  voice: string;
  temperature: number;
  max_tokens: number;
  voice_enabled: boolean;
  auto_scroll: boolean;
  font_size: 'small' | 'medium' | 'large';
  notifications: boolean;
}

// WebSocket types
export interface WebSocketMessage {
  type: 'message' | 'join_conversation' | 'ping' | 'pong' | 'joined_conversation' | 'error';
  content?: string;
  conversation_id?: string;
  timestamp?: string;
  error?: string;
  is_partial?: boolean;
  is_final?: boolean;
}

// UI State types
export interface UIState {
  sidebarOpen: boolean;
  settingsOpen: boolean;
  loading: boolean;
  error: string | null;
  connected: boolean;
  typing: boolean;
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}