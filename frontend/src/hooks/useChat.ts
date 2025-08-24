import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@services/api';
import { getWebSocketService } from '@services/websocket';
import { ChatMessage, Conversation, ChatRequest, WebSocketMessage } from '@types/index';

// Hook for managing chat messages and conversations
export const useChat = (conversationId?: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const wsService = useRef(getWebSocketService());
  const queryClient = useQueryClient();

  // Get conversation data
  const { data: conversation, isLoading: conversationLoading } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => conversationId ? apiService.getConversation(conversationId) : null,
    enabled: !!conversationId,
  });

  // Update messages when conversation changes
  useEffect(() => {
    if (conversation?.messages) {
      setMessages(conversation.messages);
    }
  }, [conversation]);

  // WebSocket connection management
  useEffect(() => {
    const ws = wsService.current;

    const handleConnect = () => setIsConnected(true);
    const handleDisconnect = () => setIsConnected(false);
    const handleMessage = (data: WebSocketMessage) => {
      if (data.type === 'message' && data.content) {
        const message: ChatMessage = {
          id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          content: data.content,
          role: 'assistant',
          timestamp: data.timestamp || new Date().toISOString(),
          conversation_id: data.conversation_id,
          is_partial: data.is_partial,
        };

        setMessages(prev => {
          if (data.is_partial) {
            // Update the last assistant message if it's partial
            const lastMessage = prev[prev.length - 1];
            if (lastMessage?.role === 'assistant' && lastMessage.is_partial) {
              return [
                ...prev.slice(0, -1),
                { ...lastMessage, content: message.content, is_partial: true }
              ];
            } else {
              return [...prev, { ...message, is_partial: true }];
            }
          } else {
            // Final message
            const lastMessage = prev[prev.length - 1];
            if (lastMessage?.role === 'assistant' && lastMessage.is_partial) {
              return [
                ...prev.slice(0, -1),
                { ...lastMessage, content: message.content, is_partial: false }
              ];
            } else {
              return [...prev, message];
            }
          }
        });

        setIsTyping(false);
      }
    };

    ws.on('connect', handleConnect);
    ws.on('disconnect', handleDisconnect);
    ws.on('message', handleMessage);

    // Connect if not already connected
    if (!ws.isConnected()) {
      ws.connect().catch(console.error);
    }

    // Join conversation if specified
    if (conversationId) {
      ws.joinConversation(conversationId);
    }

    return () => {
      ws.off('connect', handleConnect);
      ws.off('disconnect', handleDisconnect);
      ws.off('message', handleMessage);
    };
  }, [conversationId]);

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (request: ChatRequest) => apiService.sendMessage(request),
    onMutate: (request) => {
      // Optimistic update - add user message immediately
      const userMessage: ChatMessage = {
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        content: request.content,
        role: 'user',
        timestamp: new Date().toISOString(),
        conversation_id: request.conversation_id,
      };

      setMessages(prev => [...prev, userMessage]);
      setIsTyping(true);

      return { userMessage };
    },
    onSuccess: (response, request) => {
      // If not using WebSocket, add assistant response
      if (!isConnected) {
        const assistantMessage: ChatMessage = {
          id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          content: response.content,
          role: 'assistant',
          timestamp: response.timestamp,
          conversation_id: response.conversation_id,
          tools_used: response.tools_used,
          processing_time: response.processing_time,
        };

        setMessages(prev => [...prev, assistantMessage]);
      }

      setIsTyping(false);

      // Invalidate conversations list to update with new message
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
    onError: (error) => {
      console.error('Failed to send message:', error);
      setIsTyping(false);
      
      // Remove the optimistic user message on error
      setMessages(prev => prev.slice(0, -1));
    },
  });

  const sendMessage = useCallback((content: string, options?: Partial<ChatRequest>) => {
    const request: ChatRequest = {
      content,
      conversation_id: conversationId,
      ...options,
    };

    if (isConnected) {
      // Use WebSocket for real-time messaging
      try {
        wsService.current.sendMessage(content, conversationId);
        
        // Still add user message optimistically
        const userMessage: ChatMessage = {
          id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          content,
          role: 'user',
          timestamp: new Date().toISOString(),
          conversation_id: conversationId,
        };
        
        setMessages(prev => [...prev, userMessage]);
        setIsTyping(true);
      } catch (error) {
        console.error('WebSocket send failed, falling back to HTTP:', error);
        sendMessageMutation.mutate(request);
      }
    } else {
      // Fallback to HTTP API
      sendMessageMutation.mutate(request);
    }
  }, [conversationId, isConnected, sendMessageMutation]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    sendMessage,
    clearMessages,
    isTyping,
    isConnected,
    isLoading: conversationLoading || sendMessageMutation.isPending,
    error: sendMessageMutation.error,
  };
};

// Hook for managing conversations list
export const useConversations = () => {
  const queryClient = useQueryClient();

  const {
    data: conversations = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['conversations'],
    queryFn: apiService.getConversations,
    staleTime: 30000, // Consider data stale after 30 seconds
  });

  const createConversationMutation = useMutation({
    mutationFn: (title?: string) => apiService.createConversation(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  const deleteConversationMutation = useMutation({
    mutationFn: apiService.deleteConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  const clearConversationMutation = useMutation({
    mutationFn: apiService.clearConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  return {
    conversations,
    isLoading,
    error,
    createConversation: createConversationMutation.mutate,
    deleteConversation: deleteConversationMutation.mutate,
    clearConversation: clearConversationMutation.mutate,
    isCreating: createConversationMutation.isPending,
    isDeleting: deleteConversationMutation.isPending,
    isClearing: clearConversationMutation.isPending,
  };
};

// Hook for system health and status
export const useSystemStatus = () => {
  return useQuery({
    queryKey: ['system-health'],
    queryFn: apiService.getHealth,
    refetchInterval: 10000, // Refetch every 10 seconds
    retry: 2,
  });
};

// Hook for available models
export const useModels = () => {
  return useQuery({
    queryKey: ['models'],
    queryFn: apiService.getModels,
    staleTime: 300000, // 5 minutes
  });
};

// Hook for available tools
export const useTools = () => {
  return useQuery({
    queryKey: ['tools'],
    queryFn: apiService.getTools,
    staleTime: 300000, // 5 minutes
  });
};