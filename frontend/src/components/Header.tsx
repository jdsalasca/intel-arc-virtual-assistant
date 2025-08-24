import React from 'react';
import { Menu, Settings, Mic, MicOff, Sun, Moon, Monitor } from 'lucide-react';
import { AppSettings } from '@types/index';

interface HeaderProps {
  onSidebarToggle: () => void;
  onSettingsOpen: () => void;
  settings: AppSettings;
  onSettingsChange: (settings: AppSettings) => void;
  systemHealth?: {
    status: string;
    service: string;
    version: string;
  };
}

const Header: React.FC<HeaderProps> = ({
  onSidebarToggle,
  onSettingsOpen,
  settings,
  onSettingsChange,
  systemHealth
}) => {
  const toggleTheme = () => {
    const themes = ['light', 'dark', 'system'] as const;
    const currentIndex = themes.indexOf(settings.theme);
    const nextTheme = themes[(currentIndex + 1) % themes.length];
    onSettingsChange({ ...settings, theme: nextTheme });
  };

  const toggleVoice = () => {
    onSettingsChange({ ...settings, voice_enabled: !settings.voice_enabled });
  };

  const getThemeIcon = () => {
    switch (settings.theme) {
      case 'light':
        return <Sun size={20} />;
      case 'dark':
        return <Moon size={20} />;
      case 'system':
        return <Monitor size={20} />;
      default:
        return <Sun size={20} />;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-500';
      case 'warning':
        return 'text-yellow-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Left Section */}
        <div className="flex items-center space-x-4">
          <button
            onClick={onSidebarToggle}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 lg:hidden"
            title="Toggle sidebar"
          >
            <Menu size={20} className="text-gray-600 dark:text-gray-400" />
          </button>
          
          <div className="hidden lg:block">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              WiWin AI Assistant
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Intel-Optimized Conversational AI
            </p>
          </div>
        </div>

        {/* Center Section - Status */}
        <div className="hidden md:flex items-center space-x-2">
          {systemHealth && (
            <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800">
              <div className={`w-2 h-2 rounded-full ${getStatusColor(systemHealth.status)}`} />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {systemHealth.status === 'healthy' ? 'Online' : 'Offline'}
              </span>
            </div>
          )}
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-2">
          {/* Voice Toggle */}
          <button
            onClick={toggleVoice}
            className={`p-2 rounded-lg transition-colors ${
              settings.voice_enabled
                ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'
            }`}
            title={settings.voice_enabled ? 'Disable voice' : 'Enable voice'}
          >
            {settings.voice_enabled ? <Mic size={20} /> : <MicOff size={20} />}
          </button>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            title={`Current theme: ${settings.theme}`}
          >
            {getThemeIcon()}
          </button>

          {/* Settings */}
          <button
            onClick={onSettingsOpen}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            title="Open settings"
          >
            <Settings size={20} />
          </button>
        </div>
      </div>

      {/* Mobile Status */}
      <div className="md:hidden mt-2">
        {systemHealth && (
          <div className="flex items-center justify-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${getStatusColor(systemHealth.status)}`} />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              System {systemHealth.status === 'healthy' ? 'Online' : 'Offline'}
            </span>
            {systemHealth.version && (
              <span className="text-xs text-gray-400 dark:text-gray-500">
                v{systemHealth.version}
              </span>
            )}
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;