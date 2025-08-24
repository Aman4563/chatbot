import React, { RefObject } from 'react';
import 'highlight.js/styles/atom-one-dark.css';
import { 
  ChevronLeft, 
  ChevronRight, 
  ChevronDown, 
  Copy, 
  Check, 
  Edit3, 
  RotateCcw, 
  User, 
  Bot, 
  MessageCircle,
  X,
  FileText,
  Image as ImageIcon
} from 'lucide-react';
import { Conversation, Message, FileData } from '../chatSlice';
import { CHAT_CONSTANTS } from '../constants/chatConstants';
import { MarkdownRenderer } from './shared/MarkdownRenderer';
import { FileIcon } from './shared/FileIcon';

interface ChatMessagesProps {
  activeConversation: Conversation;
  isLoading: boolean;
  collapsedBlocks: Set<string>;
  copiedCode: string;
  onNavigateUserEdit: (messageId: string, direction: 'prev' | 'next') => void;
  onNavigateResponse: (messageId: string, direction: 'prev' | 'next') => void;
  onRegenerateResponse: (messageId: string) => void;
  onToggleCodeBlock: (blockId: string) => void;
  onCopyCode: (text: string, blockId: string) => void;
  onToggleEdit: (messageId: string) => void;
  onRegenerateFromMessage: (messageId: string, newText: string, files: FileData[]) => void;
  messagesEndRef: RefObject<HTMLDivElement>;
}



// Code block component
const CodeBlock = ({ 
  className, 
  children, 
  onToggleCodeBlock, 
  onCopyCode, 
  collapsedBlocks, 
  copiedCode 
}: any) => {
  const code = String(children).replace(/\n$/, '');
  const language = className?.replace(/language-/, '') || 'text';
  const blockId = `code-${Math.random().toString(36).substr(2, 9)}`;
  const isCollapsed = collapsedBlocks.has(blockId);
  const lines = code.split('\n');
  const shouldShowCollapse = lines.length > CHAT_CONSTANTS.CODE_COLLAPSE_THRESHOLD;

  return (
    <div className="my-4 rounded-lg overflow-hidden border border-gray-200 shadow-sm bg-white">
      <div className="bg-gray-50 px-4 py-2.5 flex items-center justify-between border-b border-gray-200">
        <div className="flex items-center gap-3">
          {shouldShowCollapse && (
            <button
              onClick={() => onToggleCodeBlock(blockId)}
              className="text-gray-500 hover:text-gray-700 transition-colors p-1 rounded hover:bg-gray-200"
              title={isCollapsed ? "Expand code" : "Collapse code"}
            >
              {isCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          )}
          <span className="text-gray-600 text-sm font-medium capitalize">
            {language === 'text' ? 'Code' : language}
          </span>
          <span className="text-gray-500 text-xs">
            {lines.length} line{lines.length !== 1 ? 's' : ''}
          </span>
        </div>
        <button
          onClick={() => onCopyCode(code, blockId)}
          className="flex items-center gap-2 px-2.5 py-1 bg-white hover:bg-gray-100 text-gray-600 text-sm rounded border border-gray-300 transition-all duration-200"
          title="Copy code"
        >
          {copiedCode === blockId ? (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {!isCollapsed && (
        <div className="relative">
          <pre className="bg-gray-900 text-gray-100 p-4 overflow-x-auto text-sm font-mono leading-relaxed custom-scrollbar max-h-96 overflow-y-auto">
            <code className={`language-${language}`}>
              {children}
            </code>
          </pre>
        </div>
      )}

      {isCollapsed && (
        <div className="bg-gray-50 px-4 py-3 text-sm text-gray-600">
          <span className="italic">Code block collapsed ({lines.length} lines)</span>
        </div>
      )}
    </div>
  );
};

// Editable message component
const EditableMessage = ({ 
  msg, 
  onSave, 
  onCancel 
}: {
  msg: Message;
  onSave: (text: string) => void;
  onCancel: () => void;
}) => {
  const [editText, setEditText] = React.useState(msg.text);

  const handleSave = () => {
    if (editText.trim()) {
      onSave(editText.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      onCancel();
    }
  };

  return (
    <div className="space-y-3">
      {/* Edit Form */}
      <div className="bg-white/95 backdrop-blur-sm rounded-lg p-4 border border-gray-200 shadow-sm">
        <textarea
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full p-3 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-800 bg-white shadow-sm transition-all duration-200"
          rows={Math.max(2, editText.split('\n').length)}
          autoFocus
          placeholder="Type your message..."
        />
      </div>
      
      {/* Action Bar */}
      <div className="flex justify-center">
        <div className="flex items-center gap-1 bg-white/95 backdrop-blur-sm rounded-lg px-2 py-1 shadow-sm border border-gray-200/50">
          <button
            onClick={onCancel}
            className="p-1.5 hover:bg-gray-100 rounded-md transition-colors group" 
            title="Cancel editing"
          >
            <X className="w-4 h-4 text-gray-500 group-hover:text-gray-700" />
          </button>
          
          <div className="w-px h-4 bg-gray-300 mx-1"></div>
          
          <button
            onClick={handleSave}
            className="p-1.5 hover:bg-green-100 rounded-md transition-colors group disabled:opacity-40 disabled:hover:bg-transparent"
            disabled={!editText.trim()}
            title="Save & regenerate"
          >
            <Check className="w-4 h-4 text-gray-500 group-hover:text-green-600" />
          </button>
        </div>
      </div>
    </div>
  );
};

// File preview in message
const MessageFilePreview = ({ file, index }: { file: FileData; index: number }) => {
  const isImage = file.mime_type.startsWith('image/');

  if (isImage) {
    return (
      <div key={index} className="relative inline-block m-1 group">
        <img
          src={file.url || `data:${file.mime_type};base64,${file.data}`}
          alt={file.filename}
          className="max-w-full sm:max-w-xs max-h-48 sm:max-h-64 rounded-xl object-cover border border-gray-200 shadow-sm cursor-pointer hover:shadow-lg transition-all duration-200"
          onClick={() => window.open(file.url || `data:${file.mime_type};base64,${file.data}`, '_blank')}
        />
      </div>
    );
  } else {
    return (
      <div key={index} className="inline-flex items-center gap-1 sm:gap-2 m-1 px-2 sm:px-3 py-1.5 sm:py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-xl text-xs sm:text-sm transition-all duration-200">
        <div className="flex items-center gap-1 sm:gap-2 text-gray-700">
          <FileIcon mimeType={file.mime_type} className="w-3 h-3 sm:w-4 sm:h-4" />
          <span className="truncate max-w-20 sm:max-w-32 font-medium">{file.filename}</span>
        </div>
      </div>
    );
  }
};

// Enhanced typing indicator component
const TypingIndicator = () => {
  return (
    <div className="flex items-center space-x-2 py-3">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div>
        <div className="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div>
        <div className="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div>
      </div>
      <span className="text-gray-500 text-sm">AI is thinking...</span>
    </div>
  );
};

// Enhanced streaming text component with smooth updates
const StreamingText = ({ text, isComplete }: { text: string; isComplete: boolean }) => {
  return <MarkdownRenderer isStreaming={!isComplete}>{text}</MarkdownRenderer>;
};

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  activeConversation,
  isLoading,
  collapsedBlocks,
  copiedCode,
  onNavigateUserEdit,
  onNavigateResponse,
  onRegenerateResponse,
  onToggleCodeBlock,
  onCopyCode,
  onToggleEdit,
  onRegenerateFromMessage,
  messagesEndRef
}) => {
  return (
    <div className="flex-1 overflow-y-auto bg-transparent custom-scrollbar h-full">
      <div className="w-full max-w-4xl mx-auto px-3 sm:px-4 md:px-6 py-4 sm:py-6 min-h-full">
        {activeConversation.messages.length === 0 && !isLoading && (
          <div className="text-center py-12 sm:py-16 md:py-20">
            <div className="relative mb-6 sm:mb-8 mx-auto w-24 h-24 sm:w-28 sm:h-28 md:w-32 md:h-32">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-indigo-600 rounded-3xl shadow-2xl transform rotate-3 animate-pulse"></div>
              <div className="relative w-full h-full bg-white rounded-3xl shadow-xl flex items-center justify-center transform -rotate-3 hover:rotate-0 transition-transform duration-500">
                <MessageCircle className="w-10 h-10 sm:w-12 sm:h-12 md:w-16 md:h-16 text-blue-600" />
              </div>
            </div>
            <h4 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-gray-800 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-4">
              Welcome to Xbot!
            </h4>
            <p className="text-gray-600 mb-6 sm:mb-8 text-base sm:text-lg leading-relaxed max-w-xl mx-auto px-4">
              Your intelligent AI assistant powered by multiple advanced language models. 
              <br />Ready to help with questions, analysis, creativity, and more.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 max-w-2xl mx-auto mb-6 sm:mb-8 px-4">
              <div className="group p-3 sm:p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl border border-blue-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <div className="w-6 h-6 sm:w-8 sm:h-8 bg-blue-500 rounded-xl flex items-center justify-center mb-1 sm:mb-2 mx-auto group-hover:scale-110 transition-transform">
                  <MessageCircle className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                </div>
                <span className="text-blue-800 text-xs sm:text-sm font-semibold">Chat</span>
              </div>
              <div className="group p-3 sm:p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-2xl border border-green-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <div className="w-6 h-6 sm:w-8 sm:h-8 bg-green-500 rounded-xl flex items-center justify-center mb-1 sm:mb-2 mx-auto group-hover:scale-110 transition-transform">
                  <FileText className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                </div>
                <span className="text-green-800 text-xs sm:text-sm font-semibold">Documents</span>
              </div>
              <div className="group p-3 sm:p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl border border-purple-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <div className="w-6 h-6 sm:w-8 sm:h-8 bg-purple-500 rounded-xl flex items-center justify-center mb-1 sm:mb-2 mx-auto group-hover:scale-110 transition-transform">
                  <ImageIcon className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                </div>
                <span className="text-purple-800 text-xs sm:text-sm font-semibold">Images</span>
              </div>
              <div className="group p-3 sm:p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-2xl border border-orange-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <div className="w-6 h-6 sm:w-8 sm:h-8 bg-orange-500 rounded-xl flex items-center justify-center mb-1 sm:mb-2 mx-auto group-hover:scale-110 transition-transform">
                  <Bot className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                </div>
                <span className="text-orange-800 text-xs sm:text-sm font-semibold">Analysis</span>
              </div>
            </div>
            <p className="text-sm text-gray-500">
              💡 Try asking questions, uploading files, or generating images
            </p>
          </div>
        )}

        {activeConversation.messages.map((msg, idx) => (
          <div key={msg.id || idx} className={`mb-4 sm:mb-6 ${msg.sender === 'User' ? 'group' : ''}`}>
            <div className={`flex ${msg.sender === 'User' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex gap-2 sm:gap-3 md:gap-4 ${msg.sender === 'User' ? 'max-w-sm sm:max-w-md md:max-w-lg' : 'max-w-full sm:max-w-3xl lg:max-w-4xl'} ${msg.sender === 'User' ? 'flex-row-reverse' : 'flex-row'}`}>
              {/* Avatar */}
              <div className={`
                w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 rounded-2xl flex items-center justify-center flex-shrink-0 mt-1 shadow-lg ring-2 ring-white
                ${msg.sender === 'User'
                  ? 'bg-gradient-to-br from-green-500 to-emerald-600'
                  : 'bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600'
                }
              `}>
                {msg.sender === 'User' ? (
                  <User className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                ) : (
                  <Bot className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                )}
              </div>

              {/* Message Content */}
              <div className={`
                px-3 sm:px-4 md:px-5 py-3 sm:py-4 rounded-2xl shadow-lg border backdrop-blur-sm relative group transition-all duration-200 hover:shadow-xl
                ${msg.sender === 'User'
                  ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white border-blue-600/20 flex-shrink'
                  : 'bg-white/95 text-gray-800 border-gray-200/50 hover:bg-white flex-1'
                }
                ${msg.sender === 'User' ? 'rounded-tr-lg' : 'rounded-tl-lg'}
              `}>
                {/* Bot Action buttons - only for bot messages */}
                {msg.sender === 'Bot' && (
                  <div className="absolute top-1 sm:top-2 right-1 sm:right-2 flex items-center space-x-1 sm:space-x-2 opacity-0 group-hover:opacity-100 transition-all duration-300">

                    {/* Bot message navigation and regenerate buttons */}
                    {!msg.isStreaming && !isLoading && (
                      <>
                        {msg.responses && msg.responses.length > 1 && (
                          <div className="flex items-center gap-1 bg-white/90 rounded-lg p-0.5 sm:p-1 shadow-sm border border-gray-200">
                            <button
                              onClick={() => onNavigateResponse(msg.id, 'prev')}
                              disabled={(msg.currentResponseIndex || 0) === 0}
                              className="p-0.5 sm:p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                              title="Previous response"
                            >
                              <ChevronLeft className="w-3 h-3 sm:w-4 sm:h-4 text-gray-600" />
                            </button>

                            <span className="text-xs text-gray-500 px-1 sm:px-2 font-medium">
                              {(msg.currentResponseIndex || 0) + 1} / {msg.responses.length}
                            </span>

                            <button
                              onClick={() => onNavigateResponse(msg.id, 'next')}
                              disabled={(msg.currentResponseIndex || 0) === (msg.responses?.length || 1) - 1}
                              className="p-0.5 sm:p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                              title="Next response"
                            >
                              <ChevronRight className="w-3 h-3 sm:w-4 sm:h-4 text-gray-600" />
                            </button>
                          </div>
                        )}

                        <button
                          onClick={() => onRegenerateResponse(msg.id)}
                          className="p-1 sm:p-1.5 bg-white/90 hover:bg-gray-100 rounded-lg shadow-sm border border-gray-200 transition-all duration-200"
                          title="Regenerate response"
                        >
                          <RotateCcw className="w-3 h-3 sm:w-4 sm:h-4 text-gray-600" />
                        </button>
                      </>
                    )}
                  </div>
                )}

                {/* Message content rendering */}
                {msg.isEditing ? (
                  <EditableMessage
                    msg={msg}
                    onSave={(newText) => {
                      onRegenerateFromMessage(msg.id, newText, msg.files || []);
                    }}
                    onCancel={() => onToggleEdit(msg.id)}
                  />
                ) : (
                  <>
                    {/* Show typing indicator only if it's a bot message that just started streaming */}
                    {msg.sender === 'Bot' && msg.isStreaming && !msg.text && (
                      <TypingIndicator />
                    )}

                    {/* Message Text Content */}
                    {msg.text && (
                      <div className="mb-3 last:mb-0">
                        {msg.sender === 'User' ? (
                          <div className="whitespace-pre-wrap leading-relaxed text-sm sm:text-[15px]">{msg.text}</div>
                        ) : msg.isStreaming ? (
                          <StreamingText text={msg.text} isComplete={false} />
                        ) : (
                          <div className="text-gray-800">
                            <MarkdownRenderer 
                              codeBlockComponent={(props: any) => (
                                <CodeBlock 
                                  onToggleCodeBlock={onToggleCodeBlock}
                                  onCopyCode={onCopyCode}
                                  collapsedBlocks={collapsedBlocks}
                                  copiedCode={copiedCode}
                                  {...props}
                                />
                              )}
                            >
                              {msg.text}
                            </MarkdownRenderer>
                          </div>
                        )}
                      </div>
                    )}

                    {msg.files && msg.files.length > 0 && (
                      <div className="mt-4">
                        {msg.files.map((file, fileIndex) => (
                          <MessageFilePreview key={fileIndex} file={file} index={fileIndex} />
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
              </div>
            </div>
            
            {/* User Message Actions Bar */}
            {msg.sender === 'User' && !msg.isEditing && (
              <div className="flex justify-end mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <div className="flex items-center gap-0.5 bg-white/95 backdrop-blur-sm rounded-md px-1.5 py-0.5 shadow-sm border border-gray-200/50">
                  {/* Copy Message Button */}
                  <button
                    onClick={() => navigator.clipboard.writeText(msg.text)}
                    className="p-1 hover:bg-gray-100 rounded transition-colors group" 
                    title="Copy message"
                  >
                    <svg className="w-3.5 h-3.5 text-gray-500 group-hover:text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                  
                  {/* Edit Message Button */}
                  {!isLoading && (
                    <button
                      onClick={() => onToggleEdit(msg.id)}
                      className="p-1 hover:bg-gray-100 rounded transition-colors group"
                      title="Edit message"
                    >
                      <Edit3 className="w-3.5 h-3.5 text-gray-500 group-hover:text-gray-700" />
                    </button>
                  )}
                  
                  {/* Navigation for multiple versions */}
                  {((msg.edits && msg.edits.length > 1) || (msg.branches && msg.branches.length > 1)) && !isLoading && (
                    <>
                      <div className="w-px h-3 bg-gray-300 mx-0.5"></div>
                      <button
                        onClick={() => onNavigateUserEdit(msg.id, 'prev')}
                        disabled={
                          msg.edits && msg.edits.length > 1
                            ? (msg.currentEditIndex ?? msg.edits.length - 1) === 0
                            : (msg.currentBranchIndex ?? 0) === 0
                        }
                        className="p-1 hover:bg-gray-100 rounded transition-colors group disabled:opacity-40 disabled:hover:bg-transparent"
                        title="Previous version"
                      >
                        <ChevronLeft className="w-3.5 h-3.5 text-gray-500 group-hover:text-gray-700" />
                      </button>
                      
                      <span className="px-1.5 py-0.5 text-xs font-medium text-gray-600">
                        {msg.edits && msg.edits.length > 1
                          ? `${(msg.currentEditIndex ?? msg.edits.length - 1) + 1}/${msg.edits.length}`
                          : `${(msg.currentBranchIndex ?? 0) + 1}/${msg.branches?.length || 1}`
                        }
                      </span>
                      
                      <button
                        onClick={() => onNavigateUserEdit(msg.id, 'next')}
                        disabled={
                          msg.edits && msg.edits.length > 1
                            ? (msg.currentEditIndex ?? msg.edits.length - 1) === msg.edits.length - 1
                            : (msg.currentBranchIndex ?? 0) === (msg.branches?.length || 1) - 1
                        }
                        className="p-1 hover:bg-gray-100 rounded transition-colors group disabled:opacity-40 disabled:hover:bg-transparent"
                        title="Next version"
                      >
                        <ChevronRight className="w-3.5 h-3.5 text-gray-500 group-hover:text-gray-700" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};
