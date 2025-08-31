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
    <div className="chat-input-container backdrop-blur-md border-t chat-input-border shadow-2xl relative z-40 safe-area-inset">
      <div className="max-w-5xl mx-auto px-3 sm:px-4 md:px-6 py-3 sm:py-4">
        {/* Main Input Container */}
        <div className="relative chat-input-main rounded-2xl shadow-lg border chat-input-main-border overflow-visible hover:shadow-xl transition-all duration-300">
          {/* Tools Bar */}
          <div className="flex items-center justify-between px-3 sm:px-4 py-2 sm:py-3 chat-input-tools-bg border-b chat-input-tools-border overflow-visible">
            <div className="dropdown-container relative">
              {/* Aggregated tools dropdown trigger */}
                              <button
                  className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg border transition-all duration-200 ${
                    showToolTips 
                      ? 'chat-input-tools-button-active' 
                      : 'chat-input-tools-button'
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
                <div className="tools-dropdown absolute bottom-full mb-1 left-0 w-52 sm:w-60 z-[9999] rounded-lg border chat-input-dropdown-border chat-input-dropdown-bg shadow-xl overflow-hidden backdrop-blur-sm">
                  {/* AI Tools Section */}
                  <div className="border-b chat-input-dropdown-section-border">
                    <div className="px-3 py-2 chat-input-dropdown-header-bg border-b chat-input-dropdown-header-border">
                      <span className="text-xs font-semibold chat-input-dropdown-header-text uppercase tracking-wide">AI Tools</span>
                    </div>
                    <div className="py-1">
                      <button
                        onClick={() => { onToolChange('search'); setShowToolTips(false); }}
                        className={`w-full flex items-center gap-2 px-3 py-2 text-left chat-input-dropdown-item-hover text-xs transition-colors ${activeTool==='search'?'chat-input-dropdown-item-active':'chat-input-dropdown-item-text'}`}
                      >
                        <Search className="w-3.5 h-3.5" /> 
                        <div className="flex-1">
                          <div className="font-medium">Web Search</div>
                          <div className="text-xs chat-input-dropdown-item-subtext">Research topics online</div>
                        </div>
                      </button>
                      <button
                        onClick={() => { onToolChange('image'); setShowToolTips(false); }}
                        className={`w-full flex items-center gap-2 px-3 py-2 text-left chat-input-dropdown-item-hover text-xs transition-colors ${activeTool==='image'?'chat-input-dropdown-item-active':'chat-input-dropdown-item-text'}`}
                      >
                        <Image className="w-3.5 h-3.5" /> 
                        <div className="flex-1">
                          <div className="font-medium">Generate Image</div>
                          <div className="text-xs chat-input-dropdown-item-subtext">Create AI-generated images</div>
                        </div>
                      </button>
                    </div>
                  </div>
                  
                  {/* File Tools Section */}
                  <div>
                    <div className="px-3 py-2 chat-input-dropdown-header-bg border-b chat-input-dropdown-header-border">
                      <span className="text-xs font-semibold chat-input-dropdown-header-text uppercase tracking-wide">File Tools</span>
                    </div>
                    <div className="py-1">
                                            <button
                        onClick={() => { onFileUpload(); setShowToolTips(false); }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            onFileUpload();
                            setShowToolTips(false);
                          }
                        }}
                        className="w-full flex items-center gap-2 px-3 py-2 text-left chat-input-dropdown-item-hover text-xs transition-colors chat-input-dropdown-item-text"
                        aria-describedby="file-upload-description"
                      >
                        <Paperclip className="w-3.5 h-3.5" /> 
                        <div className="flex-1">
                          <div className="font-medium">Upload Files</div>
                          <div 
                            id="file-upload-description"
                            className="text-xs chat-input-dropdown-item-subtext"
                          >
                            Add documents & images
                          </div>
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
                <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-blue-100 to-purple-100 border border-blue-200 rounded-xl shadow-sm">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-xs font-semibold text-blue-800">
                    {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}
                  </span>
                  <Paperclip className="w-3 h-3 text-blue-600" />
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
              placeholder={`Type your ${activeTool === 'chat' ? 'message' : activeTool === 'search' ? 'search query' : 'image description'}...`}
              disabled={isLoading}
              className="w-full px-4 sm:px-4 py-3 sm:py-4 pr-12 sm:pr-16 border-0 resize-none outline-none bg-transparent chat-input-textarea-text placeholder-gray-500 dark:placeholder-gray-400 text-sm sm:text-[15px] leading-relaxed min-h-[50px] sm:min-h-[60px] max-h-40 sm:max-h-48 disabled:opacity-50 disabled:cursor-not-allowed custom-scrollbar touch-target"
              rows={1}
            />

            {/* Character Count */}
            {input.length > 50 && (
              <div className="absolute bottom-2 left-3 sm:left-4 text-xs chat-input-char-count hidden sm:block">
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
