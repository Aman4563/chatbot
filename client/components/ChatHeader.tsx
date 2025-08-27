import React from 'react';
import { Bot, Check, MessageSquare, Sparkles, Zap, Settings as SettingsIcon } from 'lucide-react';
import { Conversation } from '../chatSlice';
import { getModelProvider } from '../utils/modelUtils';

interface ChatHeaderProps {
  selectedModel: string;
  activeConversation: Conversation;
  copiedChat: boolean;
  onCopyChat: () => void;
  onOpenSettings: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  selectedModel,
  activeConversation,
  copiedChat,
  onCopyChat,
  onOpenSettings
}) => {
  const provider = getModelProvider(selectedModel);

  return (
    <div className="relative">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-50 via-purple-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900"></div>
      
      {/* Header content */}
      <div className="sticky top-0 z-10 px-4 sm:px-6 py-4 border-b border-gray-200/60 dark:border-gray-700/60 bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          {/* Left side - Branding */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg transform rotate-3 hover:rotate-0 transition-transform duration-300">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                <Sparkles className="w-2.5 h-2.5 text-white" />
              </div>
            </div>
            
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-gray-800 via-blue-800 to-purple-800 bg-clip-text text-transparent">
                  Xbot
                </h1>
                <div className="hidden sm:flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-xs font-semibold">
                  <Zap className="w-3 h-3" />
                  AI Assistant
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${provider.color}`}></div>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 font-medium">
                  Powered by <span className="text-gray-800 dark:text-gray-200 font-semibold">{provider.name}</span>
                </p>
                <div className="hidden sm:block w-1 h-1 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
                <p className="hidden sm:block text-xs text-gray-500 dark:text-gray-400">{selectedModel}</p>
              </div>
            </div>
          </div>
          
          {/* Right side - Actions */}
          <div className="flex items-center gap-3">
            {/* Settings Button */}
            <button
              onClick={onOpenSettings}
              className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 text-sm rounded-xl transition-all duration-200 border border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 shadow-sm hover:shadow-md group"
              title="Settings"
            >
              <SettingsIcon className="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span className="hidden sm:inline font-medium">Settings</span>
            </button>

            {/* Copy Chat Button */}
            {activeConversation.messages.length > 0 && (
              <button
                onClick={onCopyChat}
                className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 text-sm rounded-xl transition-all duration-200 border border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 shadow-sm hover:shadow-md group"
                title="Copy chat as markdown"
              >
                {copiedChat ? (
                  <>
                    <Check className="w-4 h-4 text-green-600 dark:text-green-400" />
                    <span className="hidden sm:inline font-medium text-green-600 dark:text-green-400">Copied!</span>
                  </>
                ) : (
                  <>
                    <MessageSquare className="w-4 h-4 group-hover:scale-110 transition-transform" />
                    <span className="hidden sm:inline font-medium">Export</span>
                  </>
                )}
              </button>
            )}
            
            {/* Online Status */}
            <div className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/30 dark:to-emerald-900/30 text-green-700 dark:text-green-400 text-xs font-semibold rounded-xl border border-green-200/60 dark:border-green-700/60 shadow-sm">
              <div className="relative">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div className="absolute inset-0 w-2 h-2 bg-green-400 rounded-full animate-ping"></div>
              </div>
              <span className="hidden sm:inline">Online</span>
            </div>
            
            {/* Message count */}
            {activeConversation.messages.length > 0 && (
              <div className="hidden sm:flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-lg text-xs">
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