import React, { useState, useRef, useEffect, RefObject } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../store';
import { setInput, createNewConversation, toggleMessageEdit, regenerateFromMessage, FileData } from '../chatSlice';

// Component imports
import { ChatHeader } from '../components/ChatHeader';
import { ChatMessages } from '../components/ChatMessages';
import { ChatInput } from '../components/ChatInput';
import { FilePreview } from '../components/FilePreview';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { DragOverlay } from '../components/DragOverlay';
import { EmptyState } from '../components/EmptyState';

// Custom hooks
import { useChatHandlers } from '../hooks/useChatHandlers';
import { useFileHandlers } from '../hooks/useFileHandlers';
import { useMessageActions } from '../hooks/useMessageActions';
import { useAutoScroll } from '../hooks/useAutoScroll';

const Chat: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  
  // Redux state - only extract what we actually use
  const {
    conversations,
    activeConversationId,
    input,
    isLoading,
    error,
    selectedModel,
  } = useSelector((state: RootState) => state.chat);

  // Local state
  const [selectedFiles, setSelectedFiles] = useState<FileData[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [copiedCode, setCopiedCode] = useState<string>('');
  const [collapsedBlocks, setCollapsedBlocks] = useState<Set<string>>(new Set());
  const [copiedChat, setCopiedChat] = useState(false);
  const [activeTool, setActiveTool] = useState<'chat' | 'search' | 'image'>('chat');

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Custom hooks
  const { handleSend, handleSearch, handleGenerateImage } = useChatHandlers({
    dispatch,
    activeConversationId,
    input,
    selectedFiles,
    setSelectedFiles,
    setInput: (value: string) => dispatch(setInput(value))
  });

  const {
    handleFileSelect,
    handleDrop,
    handleDragOver,
    handleDragLeave,
    removeFile
  } = useFileHandlers({
    setSelectedFiles,
    setDragOver
  });

  const {
    handleNavigateUserEdit,
    handleNavigateResponse,
    handleRegenerateResponse,
    copyToClipboard,
    toggleCodeBlock,
    copyChatAsMarkdown
  } = useMessageActions({
    dispatch,
    conversations: conversations || [],
    activeConversationId,
    setCopiedCode,
    setCollapsedBlocks,
    setCopiedChat
  });

  useAutoScroll({
    messagesEndRef: messagesEndRef as RefObject<HTMLDivElement>,
    activeConversationId,
    conversations: conversations || []
  });

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  // Create initial conversation if none exists
  useEffect(() => {
    if (conversations.length === 0) {
      dispatch(createNewConversation());
    }
  }, [conversations.length, dispatch]);

  const activeConversation = conversations.find(conv => conv.id === activeConversationId);

  // Handle tool actions
  const handleToolAction = () => {
    switch (activeTool) {
      case 'search':
        return handleSearch();
      case 'image':
        return handleGenerateImage();
      default:
        return handleSend();
    }
  };

  // Handle input change for files
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFileSelect(e.target.files);
    }
  };

  // Handle keyboard events
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && (input.trim() || selectedFiles.length > 0)) {
        return handleToolAction();
      }
    } else if (e.key === 'Enter' && e.shiftKey) {
        return handleSend();
    }
  };

  // Render empty state if no conversation
  if (!activeConversation) {
    return <EmptyState />;
  }

  return (
    <div
      className={`flex-1 flex flex-col h-full w-full bg-gradient-to-br from-gray-50 via-white to-blue-50/30 relative transition-all duration-300 ${
        dragOver ? 'bg-gradient-to-br from-blue-100 via-blue-50 to-indigo-100' : ''
        }`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      {/* Drag Overlay */}
      {dragOver && <DragOverlay />}

      {/* Header */}
      <ChatHeader
        selectedModel={selectedModel}
        activeConversation={activeConversation}
        copiedChat={copiedChat}
        onCopyChat={copyChatAsMarkdown}
      />

      {/* Messages Area */}
      <div className="flex-1 min-h-0 w-full h-full">
        <ChatMessages
          activeConversation={activeConversation}
          isLoading={isLoading}
          collapsedBlocks={collapsedBlocks}
          copiedCode={copiedCode}
          onNavigateUserEdit={handleNavigateUserEdit}
          onNavigateResponse={handleNavigateResponse}
          onRegenerateResponse={handleRegenerateResponse}
          onToggleCodeBlock={toggleCodeBlock}
          onCopyCode={copyToClipboard}
          onToggleEdit={(messageId: string) => dispatch(toggleMessageEdit(messageId))}
          onRegenerateFromMessage={(messageId: string, newText: string, files: FileData[]) =>
            dispatch(regenerateFromMessage({ messageId, newText, files }))
          }
          messagesEndRef={messagesEndRef as RefObject<HTMLDivElement>}
        />
      </div>

      {/* File Preview */}
      {selectedFiles.length > 0 && (
        <FilePreview
          files={selectedFiles}
          onRemoveFile={removeFile}
        />
      )}

      {/* Error Display */}
      {error && <ErrorDisplay error={error} />}

      {/* Input Area */}
      <ChatInput
        input={input}
        selectedFiles={selectedFiles}
        isLoading={isLoading}
        activeTool={activeTool}
        textareaRef={textareaRef}
        fileInputRef={fileInputRef}
        onInputChange={(value: string) => dispatch(setInput(value))}
        onKeyDown={handleKeyDown}
        onFileSelect={handleInputChange}
        onToolChange={setActiveTool}
        onSend={handleToolAction}
        onFileUpload={() => fileInputRef.current?.click()}
      />
    </div>
  );
};

export default Chat;
