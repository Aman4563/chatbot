import React from 'react';
import { Bot, MessageSquare, Sparkles, Zap, Settings as SettingsIcon, Menu } from 'lucide-react';
import { Conversation } from '../chatSlice';
import { getModelProvider } from '../utils/modelUtils';
import { useSidebar } from '../contexts/SidebarContext';

interface ChatHeaderProps {
  selectedModel: string;
  activeConversation: Conversation;
  onOpenSettings: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  selectedModel,
  activeConversation,
  onOpenSettings
}) => {
  const provider = getModelProvider(selectedModel);
  const { isCollapsed, isMobile, setIsCollapsed } = useSidebar();

  return (
    <div className="relative">
      {/* Background gradient */}
      <div className="absolute inset-0 header-bg-gradient"></div>
      
      {/* Header content */}
      <div className="sticky top-0 z-10 sm:px-6 py-4 border-b header-border header-bg backdrop-blur-xl">
        <div className={`mx-auto flex items-center justify-between transition-all duration-300 header-responsive ${
          isCollapsed && !isMobile ? 'sidebar-collapsed' : 'sidebar-expanded'
        }`}>
          {/* Left side - Mobile Sidebar Toggle + Branding */}
          <div className="flex items-center gap-3 sm:gap-4">
            {/* Mobile Sidebar Toggle */}
            {isMobile && (
              <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="md:hidden flex items-center justify-center w-10 h-10 header-button rounded-xl transition-all duration-200 shadow-sm hover:shadow-md"
                aria-label="Toggle sidebar"
              >
                <Menu className="w-5 h-5" />
              </button>
            )}
            <div className="relative">
              <div className="w-10 h-10 sm:w-12 sm:h-12 header-logo-bg rounded-2xl flex items-center justify-center shadow-lg transform rotate-3 hover:rotate-0 transition-transform duration-300">
                <Bot className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 sm:w-4 sm:h-4 header-sparkle-bg rounded-full flex items-center justify-center">
                <Sparkles className="w-2 h-2 sm:w-2.5 sm:h-2.5 text-white" />
              </div>
            </div>
            
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <h1 className="text-lg sm:text-xl md:text-2xl font-bold header-title-gradient bg-clip-text text-transparent header-title-text">
                  Xbot
                </h1>
                <div className="hidden sm:flex items-center gap-1 px-2 py-1 header-badge-bg header-badge-text rounded-full text-xs font-semibold">
                  <Zap className="w-3 h-3" />
                  AI Assistant
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${provider.color}`}></div>
                <p className="text-xs sm:text-sm header-subtitle-text font-medium">
                  Powered by <span className="header-subtitle-highlight font-semibold">{provider.name}</span>
                </p>
                <div className="hidden sm:block w-1 h-1 header-divider rounded-full"></div>
                <p className="hidden sm:block text-xs header-subtitle-text">{selectedModel}</p>
              </div>
            </div>
          </div>
          
          {/* Right side - Actions */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Settings Button */}
            <button
              onClick={onOpenSettings}
              className="flex items-center gap-2 px-3 py-2 header-button text-sm rounded-xl transition-all duration-200 shadow-sm hover:shadow-md group"
              title="Settings"
            >
              <SettingsIcon className="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span className="hidden sm:inline font-medium">Settings</span>
            </button>
            
            {/* Online Status - Hidden on Mobile */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-2 header-status-bg header-status-text text-xs font-semibold rounded-xl shadow-sm">
              <div className="relative">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div className="absolute inset-0 w-2 h-2 bg-green-400 rounded-full animate-ping"></div>
              </div>
              <span>Online</span>
            </div>
            
            {/* Message count - Hidden on Mobile */}
            {activeConversation.messages.length > 0 && (
              <div className="hidden md:flex items-center gap-1 px-2 py-1 header-counter-bg header-counter-text rounded-lg text-xs">
                <MessageSquare className="w-3 h-3" />
                <span>{activeConversation.messages.length}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};