import React, { RefObject, useState, useEffect } from 'react';
import { Plus, Send, Paperclip, Search, Image, MessageCircle, MoreHorizontal } from 'lucide-react';
import { FileData } from '../chatSlice';

interface ChatInputProps {
  input: string;
  selectedFiles: FileData[];
  isLoading: boolean;
  activeTool: 'chat' | 'search' | 'image';
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  fileInputRef: RefObject<HTMLInputElement | null>;
  onInputChange: (value: string) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onToolChange: (tool: 'chat' | 'search' | 'image') => void;
  onSend: () => void;
  onFileUpload: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  selectedFiles,
  isLoading,
  activeTool,
  textareaRef,
  fileInputRef,
  onInputChange,
  onKeyDown,
  onFileSelect,
  onToolChange,
  onSend,
  onFileUpload
}) => {
  const [showToolTips, setShowToolTips] = useState(false);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (showToolTips && !target.closest('.tools-dropdown')) {
        setShowToolTips(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showToolTips]);

  const getToolIcon = (tool: string) => {
    switch (tool) {
      case 'search': return <Search className="w-4 h-4" />;
      case 'image': return <Image className="w-4 h-4" />;
      default: return <MessageCircle className="w-4 h-4" />;
    }
  };

  const getToolLabel = (tool: string) => {
    switch (tool) {
      case 'search': return 'Search';
      case 'image': return 'Generate';
      default: return 'Chat';
    }
  };

  return (
    <div className="bg-white/95 backdrop-blur-md border-t border-gray-200/60 shadow-2xl relative z-40">
      <div className="max-w-5xl mx-auto px-3 sm:px-4 md:px-6 py-3 sm:py-4">
        {/* Main Input Container */}
        <div className="relative bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-visible hover:shadow-xl transition-all duration-300">
          {/* Tools Bar */}
          <div className="flex items-center justify-between px-3 sm:px-4 py-2 sm:py-3 bg-gray-50/80 border-b border-gray-200/50 overflow-visible">
            <div className="dropdown-container relative">
              {/* Aggregated tools dropdown trigger */}
              <button
                className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg border transition-all duration-200 ${
                  showToolTips 
                    ? 'bg-blue-50 border-blue-200 text-blue-700 shadow-md' 
                    : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-100 shadow-sm'
                }`}
                onClick={() => setShowToolTips(v => !v)}
                title="Tools & Actions"
              >
                <MoreHorizontal className={`w-3 h-3 sm:w-4 sm:h-4 transition-transform duration-200 ${
                  showToolTips ? 'rotate-90' : ''
                }`} />
                <span className="text-xs sm:text-sm font-medium hidden sm:inline">Tools</span>
              </button>

              {showToolTips && (
                <div className="tools-dropdown absolute bottom-full mb-1 left-0 w-52 sm:w-60 z-[9999] rounded-lg border border-gray-200 bg-white shadow-xl overflow-hidden backdrop-blur-sm">
                  {/* AI Tools Section */}
                  <div className="border-b border-gray-100">
                    <div className="px-3 py-2 bg-gray-50 border-b border-gray-100">
                      <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">AI Tools</span>
                    </div>
                    <div className="py-1">
                      <button
                        onClick={() => { onToolChange('search'); setShowToolTips(false); }}
                        className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 text-xs transition-colors ${activeTool==='search'?'text-green-600 bg-green-50 font-medium':'text-gray-700'}`}
                      >
                        <Search className="w-3.5 h-3.5" /> 
                        <div className="flex-1">
                          <div className="font-medium">Web Search</div>
                          <div className="text-xs text-gray-500">Research topics online</div>
                        </div>
                      </button>
                      <button
                        onClick={() => { onToolChange('image'); setShowToolTips(false); }}
                        className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 text-xs transition-colors ${activeTool==='image'?'text-purple-600 bg-purple-50 font-medium':'text-gray-700'}`}
                      >
                        <Image className="w-3.5 h-3.5" /> 
                        <div className="flex-1">
                          <div className="font-medium">Generate Image</div>
                          <div className="text-xs text-gray-500">Create AI-generated images</div>
                        </div>
                      </button>
                    </div>
                  </div>
                  
                  {/* File Tools Section */}
                  <div>
                    <div className="px-3 py-2 bg-gray-50 border-b border-gray-100">
                      <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">File Tools</span>
                    </div>
                    <div className="py-1">
                      <button
                        onClick={() => { onFileUpload(); setShowToolTips(false); }}
                        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 text-xs transition-colors text-gray-700"
                      >
                        <Paperclip className="w-3.5 h-3.5" /> 
                        <div className="flex-1">
                          <div className="font-medium">Upload Files</div>
                          <div className="text-xs text-gray-500">Add documents & images</div>
                        </div>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right Side: Selected files counter */}
            <div className="flex items-center gap-1 sm:gap-2">
              {selectedFiles.length > 0 && (
                <div className="flex items-center gap-1 px-1.5 sm:px-2 py-0.5 sm:py-1 bg-blue-50 text-blue-600 rounded-lg border border-blue-200">
                  <span className="text-xs font-medium">{selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}</span>
                </div>
              )}
            </div>
          </div>

          {/* Input Area */}
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={`Type your ${activeTool === 'chat' ? 'message' : activeTool === 'search' ? 'search query' : 'image description'}... ${window.innerWidth > 640 ? '(Shift+Enter for new line)' : ''}`}
              disabled={isLoading}
              className="w-full px-3 sm:px-4 py-3 sm:py-4 pr-12 sm:pr-16 border-0 resize-none outline-none bg-transparent text-gray-800 placeholder-gray-500 text-sm sm:text-[15px] leading-relaxed min-h-[50px] sm:min-h-[60px] max-h-40 sm:max-h-48 disabled:opacity-50 disabled:cursor-not-allowed custom-scrollbar"
              rows={1}
            />

            {/* Character Count */}
            {input.length > 50 && (
              <div className="absolute bottom-2 left-3 sm:left-4 text-xs text-gray-400 hidden sm:block">
                {input.length} characters
              </div>
            )}

            {/* Send Button */}
            <div className="absolute bottom-2 sm:bottom-3 right-2 sm:right-3">
              <button
                onClick={onSend}
                disabled={isLoading || (!input.trim() && selectedFiles.length === 0)}
                className={`w-8 h-8 sm:w-10 sm:h-10 rounded-xl transition-all duration-200 flex items-center justify-center shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95 ${
                  isLoading || (!input.trim() && selectedFiles.length === 0)
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : activeTool === 'search' 
                      ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:from-green-600 hover:to-emerald-700'
                      : activeTool === 'image'
                        ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white hover:from-purple-600 hover:to-pink-700'
                        : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700'
                }`}
                title={activeTool === 'chat' ? 'Send message' : activeTool === 'search' ? 'Search' : 'Generate image'}
              >
                {isLoading ? (
                  <div className="w-3 h-3 sm:w-4 sm:h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : activeTool === 'search' ? (
                  <Search className="w-3 h-3 sm:w-4 sm:h-4" />
                ) : activeTool === 'image' ? (
                  <Image className="w-3 h-3 sm:w-4 sm:h-4" />
                ) : (
                  <Send className="w-3 h-3 sm:w-4 sm:h-4" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Helper Text */}
        <div className="flex items-center justify-between mt-2 sm:mt-3 px-1 sm:px-2">
          <div className="flex items-center gap-3 sm:gap-6 text-xs text-gray-500">
            <span className="flex items-center gap-1 sm:gap-1.5">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
              <span className="hidden sm:inline">Drag & drop files anywhere</span>
              <span className="sm:hidden">Drop files</span>
            </span>
            <span className="hidden sm:inline">Shift+Enter for new line</span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 text-xs text-gray-400">
            {activeTool === 'search' && (
              <span className="flex items-center gap-1">
                <Search className="w-3 h-3" />
                <span className="hidden sm:inline">Web search mode</span>
                <span className="sm:hidden">Search</span>
              </span>
            )}
            {activeTool === 'image' && (
              <span className="flex items-center gap-1">
                <Image className="w-3 h-3" />
                <span className="hidden sm:inline">Image generation mode</span>
                <span className="sm:hidden">Image</span>
              </span>
            )}
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={onFileSelect}
          className="hidden"
          accept="image/*,.pdf,.doc,.docx,.txt,.json,.csv"
        />
      </div>
    </div>
  );
};
