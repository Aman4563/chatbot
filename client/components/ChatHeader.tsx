import React from 'react';
import { Bot, Check, MessageSquare, Sparkles, Zap } from 'lucide-react';
import { Conversation } from '../chatSlice';
import { getModelProvider } from '../utils/modelUtils';

interface ChatHeaderProps {
  selectedModel: string;
  activeConversation: Conversation;
  copiedChat: boolean;
  onCopyChat: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  selectedModel,
  activeConversation,
  copiedChat,
  onCopyChat
}) => {
  const provider = getModelProvider(selectedModel);

  return (
    <div className="relative">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-50 via-purple-50 to-indigo-50"></div>
      
      {/* Header content */}
      <div className="sticky top-0 z-10 px-4 sm:px-6 py-4 border-b border-gray-200/60 bg-white/90 backdrop-blur-xl">
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
                <div className="hidden sm:flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
                  <Zap className="w-3 h-3" />
                  AI Assistant
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${provider.color}`}></div>
                <p className="text-xs sm:text-sm text-gray-600 font-medium">
                  Powered by <span className="text-gray-800 font-semibold">{provider.name}</span>
                </p>
                <div className="hidden sm:block w-1 h-1 bg-gray-300 rounded-full"></div>
                <p className="hidden sm:block text-xs text-gray-500">{selectedModel}</p>
              </div>
            </div>
          </div>
          
          {/* Right side - Actions */}
          <div className="flex items-center gap-3">
            {/* Copy Chat Button */}
            {activeConversation.messages.length > 0 && (
              <button
                onClick={onCopyChat}
                className="flex items-center gap-2 px-3 py-2 bg-white hover:bg-gray-50 text-gray-700 hover:text-gray-900 text-sm rounded-xl transition-all duration-200 border border-gray-200 hover:border-gray-300 shadow-sm hover:shadow-md group"
                title="Copy chat as markdown"
              >
                {copiedChat ? (
                  <>
                    <Check className="w-4 h-4 text-green-600" />
                    <span className="hidden sm:inline font-medium text-green-600">Copied!</span>
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
            <div className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-green-50 to-emerald-50 text-green-700 text-xs font-semibold rounded-xl border border-green-200/60 shadow-sm">
              <div className="relative">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div className="absolute inset-0 w-2 h-2 bg-green-400 rounded-full animate-ping"></div>
              </div>
              <span className="hidden sm:inline">Online</span>
            </div>
            
            {/* Message count */}
            {activeConversation.messages.length > 0 && (
              <div className="hidden sm:flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 rounded-lg text-xs">
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
