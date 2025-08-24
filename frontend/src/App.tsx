import React, { useState, useEffect } from 'react';
import { QueryErrorResetBoundary } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';
import ChatInterface from '@components/ChatInterface';
import Sidebar from '@components/Sidebar';
import Header from '@components/Header';
import SettingsModal from '@components/SettingsModal';
import ErrorFallback from '@components/ErrorFallback';
import { useSystemStatus } from '@hooks/useChat';
import { AppSettings } from '@types/index';

// Default settings
const defaultSettings: AppSettings = {
  theme: 'dark',
  model: 'qwen2.5-7b-int4',
  voice: 'female_1',
  temperature: 0.7,
  max_tokens: 256,
  voice_enabled: false,
  auto_scroll: true,
  font_size: 'medium',
  notifications: true,
};

function App() {
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState<AppSettings>(() => {
    // Load settings from localStorage
    const saved = localStorage.getItem('app-settings');
    return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
  });

  // System status check
  const { data: systemHealth, isError: systemError } = useSystemStatus();

  // Apply theme
  useEffect(() => {
    const root = document.documentElement;
    
    if (settings.theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const updateTheme = (e: MediaQueryListEvent) => {
        root.classList.toggle('dark', e.matches);
      };
      
      root.classList.toggle('dark', mediaQuery.matches);
      mediaQuery.addEventListener('change', updateTheme);
      
      return () => mediaQuery.removeEventListener('change', updateTheme);
    } else {
      root.classList.toggle('dark', settings.theme === 'dark');
    }
  }, [settings.theme]);

  // Apply font size
  useEffect(() => {
    const root = document.documentElement;
    const fontSize = {
      small: '14px',
      medium: '16px',
      large: '18px',
    }[settings.font_size];
    
    root.style.fontSize = fontSize;
  }, [settings.font_size]);

  // Save settings to localStorage when they change
  useEffect(() => {
    localStorage.setItem('app-settings', JSON.stringify(settings));
  }, [settings]);

  const updateSettings = (updates: Partial<AppSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  };

  const selectConversation = (id: string | undefined) => {
    setCurrentConversationId(id);
    // Close sidebar on mobile when conversation is selected
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const toggleSettings = () => setSettingsOpen(!settingsOpen);

  // Show loading state if system is initializing
  if (systemHealth?.status === 'initializing') {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold mb-2">Initializing Intel Virtual Assistant</h2>
          <p className="text-muted-foreground">Setting up AI models and hardware optimization...</p>
        </div>
      </div>
    );
  }

  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          FallbackComponent={ErrorFallback}
          onReset={reset}
          resetKeys={[currentConversationId]}
        >
          <div className="flex h-screen bg-background text-foreground overflow-hidden">
            {/* Sidebar */}
            <div className={`
              fixed inset-y-0 left-0 z-50 w-80 transform transition-transform duration-300 ease-in-out
              md:relative md:translate-x-0 md:z-0
              ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            `}>
              <Sidebar
                currentConversationId={currentConversationId}
                onSelectConversation={selectConversation}
                onClose={() => setSidebarOpen(false)}
                systemHealth={systemHealth}
              />
            </div>

            {/* Sidebar overlay for mobile */}
            {sidebarOpen && (
              <div 
                className="fixed inset-0 z-40 bg-black bg-opacity-50 md:hidden"
                onClick={() => setSidebarOpen(false)}
              />
            )}

            {/* Main content */}
            <div className="flex-1 flex flex-col min-w-0">
              {/* Header */}
              <Header
                onToggleSidebar={toggleSidebar}
                onToggleSettings={toggleSettings}
                systemHealth={systemHealth}
                sidebarOpen={sidebarOpen}
              />

              {/* Chat Interface */}
              <div className="flex-1 overflow-hidden">
                <ChatInterface
                  conversationId={currentConversationId}
                  settings={settings}
                  onSettingsChange={updateSettings}
                />
              </div>
            </div>

            {/* Settings Modal */}
            <SettingsModal
              isOpen={settingsOpen}
              onClose={() => setSettingsOpen(false)}
              settings={settings}
              onSettingsChange={updateSettings}
            />
          </div>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}

export default App;