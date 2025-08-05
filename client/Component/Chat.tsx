// Chat.tsx - Complete fixed version with enhanced image handling
import React, { useRef, useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/atom-one-dark.css';
import { visit } from 'unist-util-visit';

import { 
  setInput, 
  sendChatMessageStream, 
  addMessage, 
  createNewConversation,
  toggleMessageEdit,
  regenerateFromMessage,
  navigateResponseVersion,
  regenerateResponse,
  FileData,
  Message,
  navigateUserEditVersion,
  fetchAvailableModels,
  setUserBranchIndex,
  replaceConversationTail,
  webSearch, 
  generateImage,
  addBotMessage,
  updateMessageText,
} from '../chatSlice';
import { AlertCircle, Bot, Check, ChevronDown, ChevronLeft, ChevronRight, Copy, Edit3, File, FileText, Image, MessageCircle, MessageSquare, Paperclip, Plus, RotateCcw, Send, Upload, User, X, Eye } from 'lucide-react';
import { AppDispatch } from '@/store';
import { RootState } from '@reduxjs/toolkit/query';

function rehypeStripHljs() {
  return (tree: any) => {
    visit(tree, 'element', (node: any) => {
      if (
        node.tagName === 'code' &&
        Array.isArray(node.properties?.className)
      ) {
        node.properties.className = node.properties.className.filter(
          (c: string) => c !== 'hljs'
        );
      }
    });
  };
}

const Chat = () => {
  const dispatch = useDispatch<AppDispatch>();
  const {
    conversations,
    activeConversationId,
    input,
    isLoading,
    error,
    selectedModel,
    availableModels,
    searchResults,
    searchLoading,
    searchError,
    generatedImageUrl,
    imageLoading,
    imageError,
    imageHistory,
    currentImageIndex,
  } = useSelector((state: RootState) => state.chat);

  const [selectedFiles, setSelectedFiles] = useState<FileData[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [copiedCode, setCopiedCode] = useState<string>('');
  const [collapsedBlocks, setCollapsedBlocks] = useState<Set<string>>(new Set());
  const [copiedChat, setCopiedChat] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [activeTool, setActiveTool] = useState<'chat' | 'search' | 'image'>('chat');

  const activeConversation = conversations.find(conv => conv.id === activeConversationId);

  // Search handler
  const handleSearch = async () => {
    if (!input.trim() || !activeConversationId) return;
    
    dispatch(addMessage({
      conversationId: activeConversationId,
      message: {
        id: Date.now().toString(),
        sender: 'User',
        text: input,
        timestamp: new Date().toISOString(),
      },
    }));
    
    try {
      const results: string[] = await dispatch(webSearch({ query: input })).unwrap();
      const md = results.map((url, i) => `- [${url}](${url})`).join('\n');
      dispatch(addMessage({
        conversationId: activeConversationId,
        message: {
          id: (Date.now()+1).toString(),
          sender: 'Bot',
          text: `**Search Results**\n\n${md}`,
          timestamp: new Date().toISOString(),
        },
      }));
    } catch (e) {
      console.error('Search failed:', e);
    } finally {
      dispatch(setInput(''));
    }
  };

  // ✅ FIXED Image generation handler with comprehensive validation
  const handleGenerateImage = async () => {
  if (!input.trim() || !activeConversationId) return;

  // 1) re-add the user’s message…
  dispatch(addMessage({
    conversationId: activeConversationId,
    message: {
      id: Date.now().toString(),
      sender: 'User',
      text: input,
      timestamp: new Date().toISOString(),
    },
  }));

  // 2) insert a “Generating…” placeholder
  const loadingId = (Date.now()+1).toString();
  dispatch(addMessage({
    conversationId: activeConversationId,
    message: {
      id: loadingId,
      sender: 'Bot',
      text: '🖼️ Generating image…',
      timestamp: new Date().toISOString(),
    },
  }));

  dispatch(setInput(''));  // clear input

  try {
    // 3) call the thunk and pull out `.url` if needed
    const payload = await dispatch(generateImage({ prompt: input })).unwrap();
    const raw = typeof payload === 'string'
      ? payload
      : (payload as { url: string }).url;

    // 4) sanity-check & trim away any stray `{}` or quotes
    const cleanUrl = raw.replace(/^[{"']+|[}"']+$/g, '').trim();
    if (!cleanUrl.startsWith('data:image')) {
      throw new Error(`got bad URL: ${cleanUrl}`);
    }

    const markdown = `![Generated Image](${cleanUrl})\n\n*Prompt: "${input}"*`;
    // 5) replace the loading message
    dispatch(updateMessageText({
      conversationId: activeConversationId,
      messageId: loadingId,
      newText: markdown,
    }));
  } catch (err: any) {
    console.error(err);
    dispatch(updateMessageText({
      conversationId: activeConversationId,
      messageId: loadingId,
      newText: `❌ Image generation failed: ${err.message}`,
    }));
  }
};


  // Other handlers (keeping your existing ones)
  const handleNavigateUserEdit = (messageId: string, direction: 'prev' | 'next') => {
    const conv = conversations.find(c => c.id === activeConversationId);
    if (!conv) return;

    const idx = conv.messages.findIndex(m => m.id === messageId && m.sender === 'User');
    if (idx < 0) return;
    const userMsg = conv.messages[idx];

    const oldEditIndex = userMsg.currentEditIndex ?? 0;
    let newEditIndex = direction === 'prev' ? oldEditIndex - 1 : oldEditIndex + 1;
    newEditIndex = Math.max(0, Math.min((userMsg.edits?.length ?? 1) - 1, newEditIndex));
    const newText = userMsg.edits![newEditIndex];

    dispatch(navigateUserEditVersion({ messageId, direction }));

    const oldBranch = userMsg.currentBranchIndex ?? 0;
    let newBranch = direction === 'prev' ? oldBranch - 1 : oldBranch + 1;
    newBranch = Math.max(0, Math.min((userMsg.branches?.length ?? 1) - 1, newBranch));
    dispatch(setUserBranchIndex({ messageId, branchIndex: newBranch }));

    const head = [
      ...conv.messages.slice(0, idx),
      { ...userMsg, text: newText }
    ];
    const tail = userMsg.branches ? userMsg.branches[newBranch] : [];
    dispatch(replaceConversationTail({
      conversationId: activeConversationId!,
      head,
      tail
    }));
  };

  const handleNavigateResponse = (messageId: string, direction: 'prev' | 'next') => {
    dispatch(navigateResponseVersion({ messageId, direction }));
  };

  const handleRegenerateResponse = async (messageId: string) => {
    try {
      await dispatch(regenerateResponse(messageId)).unwrap();
    } catch (error) {
      console.error('Failed to regenerate response:', error);
    }
  };

  // useEffect hooks
  useEffect(() => {
    if (conversations.length === 0) {
      dispatch(createNewConversation());
    }
  }, [conversations.length, dispatch]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConversation?.messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  // Utility functions
  const copyToClipboard = async (text: string, blockId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCode(blockId);
      setTimeout(() => setCopiedCode(''), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const toggleCodeBlock = (blockId: string) => {
    setCollapsedBlocks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(blockId)) {
        newSet.delete(blockId);
      } else {
        newSet.add(blockId);
      }
      return newSet;
    });
  };

  const copyChatAsMarkdown = async () => {
    if (!activeConversation) return;
    
    const chatMarkdown = activeConversation.messages.map(msg => {
      const sender = msg.sender === 'User' ? '**You**' : '**Xbot**';
      const timestamp = new Date(msg.timestamp).toLocaleString();
      let content = `${sender} (${timestamp}):\n\n${msg.text || ''}`;
      
      if (msg.files && msg.files.length > 0) {
        content += '\n\n*Attachments:*\n';
        msg.files.forEach(file => {
          content += `- ${file.filename} (${file.mime_type})\n`;
        });
      }
      
      return content;
    }).join('\n\n---\n\n');

    try {
      await navigator.clipboard.writeText(chatMarkdown);
      setCopiedChat(true);
      setTimeout(() => setCopiedChat(false), 2000);
    } catch (err) {
      console.error('Failed to copy chat: ', err);
    }
  };

  // Enhanced Components for rendering
  const InlineCode = ({ children, ...props }: any) => (
    <code 
      className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono"
      {...props}
    >
      {children}
    </code>
  );

  const CodeBlock = ({ className, children, ...props }: any) => {
    const code = String(children).replace(/\n$/, '');
    const language = className?.replace(/language-/, '') || 'text';
    const blockId = `code-${Math.random().toString(36).substr(2, 9)}`;
    const isCollapsed = collapsedBlocks.has(blockId);
    const lines = code.split('\n');
    const shouldShowCollapse = lines.length > 10;

    return (
      <div className="my-4 rounded-lg overflow-hidden border border-gray-200 shadow-sm bg-white">
        <div className="bg-gray-50 px-4 py-2.5 flex items-center justify-between border-b border-gray-200">
          <div className="flex items-center gap-3">
            {shouldShowCollapse && (
              <button
                onClick={() => toggleCodeBlock(blockId)}
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
            onClick={() => copyToClipboard(code, blockId)}
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
              <code className={`language-${language}`} {...props}>
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

  // File handling functions
  const handleFileSelect = async (files: FileList) => {
    const fileDataArray: FileData[] = [];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'text/plain', 'text/csv', 'application/json',
      'application/pdf', 'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];

    for (const file of Array.from(files)) {
      if (file.size > maxSize) {
        alert(`File ${file.name} is too large. Maximum size is 10MB.`);
        continue;
      }

      if (!allowedTypes.includes(file.type)) {
        alert(`File type ${file.type} is not supported.`);
        continue;
      }

      const base64 = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(file);
      });

      fileDataArray.push({
        data: base64.split(',')[1],
        mime_type: file.type,
        filename: file.name,
        url: base64
      });
    }

    setSelectedFiles(prev => [...prev, ...fileDataArray]);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files!);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSend = async () => {
    if (!activeConversationId) {
      dispatch(createNewConversation());
      return;
    }

    if (input.trim() || selectedFiles.length > 0) {
      const userMessage: Message = {
        id: Date.now().toString(),
        sender: 'User',
        text: input,
        files: selectedFiles.length > 0 ? selectedFiles : undefined,
        timestamp: new Date().toISOString(),
      };

      dispatch(addMessage({ conversationId: activeConversationId, message: userMessage }));
      
      const messageToSend = input;
      const filesToSend = [...selectedFiles];
      dispatch(setInput(''));
      setSelectedFiles([]);

      try {
        await dispatch(sendChatMessageStream({ 
          message: messageToSend, 
          files: filesToSend 
        })).unwrap();
      } catch (error) {
        console.error('Failed to send message:', error);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Editable message component
  const EditableMessage = ({ msg, onSave, onCancel }: { 
    msg: Message; 
    onSave: (text: string) => void; 
    onCancel: () => void; 
  }) => {
    const [editText, setEditText] = useState(msg.text);

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
      <div className="bg-gray-50 rounded-lg p-4 border-2 border-blue-200 mt-2">
        <textarea
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
          rows={Math.max(2, editText.split('\n').length)}
          autoFocus
        />
        <div className="flex justify-end gap-2 mt-3">
          <button
            onClick={onCancel}
            className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 flex items-center gap-1 rounded hover:bg-gray-200 transition-colors"
          >
            <X size={14} />
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1 transition-colors"
            disabled={!editText.trim()}
          >
            <Check size={14} />
            Save & Regenerate
          </button>
        </div>
      </div>
    );
  };

  // File preview functions
  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return <Image className="w-4 h-4" />;
    if (mimeType.includes('pdf')) return <FileText className="w-4 h-4" />;
    if (mimeType.includes('word')) return <FileText className="w-4 h-4" />;
    if (mimeType.includes('text')) return <File className="w-4 h-4" />;
    return <File className="w-4 h-4" />;
  };

  const renderFilePreview = (file: FileData, index: number, isInMessage = false) => {
    const isImage = file.mime_type.startsWith('image/');
    
    if (isImage) {
      return (
        <div key={index} className="relative inline-block m-1 group">
          <img 
            src={file.url || `data:${file.mime_type};base64,${file.data}`}
            alt={file.filename}
            className={`
              ${isInMessage ? 'max-w-xs max-h-64' : 'w-16 h-16'} 
              rounded-xl object-cover border border-gray-200 shadow-sm
              ${isInMessage ? 'cursor-pointer hover:shadow-lg transition-all duration-200' : ''}
            `}
            onClick={isInMessage ? () => window.open(file.url || `data:${file.mime_type};base64,${file.data}`, '_blank') : undefined}
          />
          {!isInMessage && (
            <button
              onClick={() => removeFile(index)}
              className="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs transition-all duration-200 opacity-0 group-hover:opacity-100 shadow-lg"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      );
    } else {
      return (
        <div key={index} className="inline-flex items-center gap-2 m-1 px-3 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-xl text-sm relative group transition-all duration-200">
          <div className="flex items-center gap-2 text-gray-700">
            {getFileIcon(file.mime_type)}
            <span className="truncate max-w-32 font-medium">{file.filename}</span>
          </div>
          {!isInMessage && (
            <button
              onClick={() => removeFile(index)}
              className="ml-2 text-red-500 hover:text-red-700 transition-colors duration-200 opacity-0 group-hover:opacity-100"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      );
    }
  };

  if (!activeConversation) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <div className="text-center max-w-md mx-auto px-6">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
            <MessageCircle className="w-10 h-10 text-white" />
          </div>
          <h3 className="text-2xl font-bold text-gray-800 mb-3">Welcome to Xbot</h3>
          <p className="text-gray-600 leading-relaxed">Create a new conversation to get started with our intelligent assistant</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`flex-1 flex flex-col h-screen bg-white relative transition-all duration-300 ${
        dragOver ? 'bg-blue-50' : ''
      }`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      {/* Drag Overlay */}
      {dragOver && (
        <div className="absolute inset-0 bg-blue-100/90 backdrop-blur-sm flex items-center justify-center z-50 border-2 border-dashed border-blue-400 m-4 rounded-2xl">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Upload className="w-8 h-8 text-white" />
            </div>
            <p className="text-xl font-bold text-blue-800 mb-1">Drop files here to upload</p>
            <p className="text-blue-600">Images, documents, and more</p>
          </div>
        </div>
      )}

      {/* Enhanced Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">Xbot</h3>
              <p className="text-sm text-gray-500 font-medium">Powered by {selectedModel}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {activeConversation.messages.length > 0 && (
              <button
                onClick={copyChatAsMarkdown}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded-lg transition-all duration-200 border border-gray-300 hover:border-gray-400"
                title="Copy chat as markdown"
              >
                {copiedChat ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span className="hidden sm:inline">Copied!</span>
                  </>
                ) : (
                  <>
                    <MessageSquare className="w-4 h-4" />
                    <span className="hidden sm:inline">Copy Chat</span>
                  </>
                )}
              </button>
            )}
            <div className="px-3 py-1.5 bg-green-100 text-green-800 text-xs font-semibold rounded-full border border-green-200">
              <div className="w-2 h-2 bg-green-500 rounded-full inline-block mr-2 animate-pulse"></div>
              Online
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto bg-gradient-to-b from-gray-50 to-gray-100 custom-scrollbar">
        <div className="w-full mx-auto px-4 py-6">
          {activeConversation.messages.length === 0 && !isLoading && (
            <div className="text-center py-16">
              <div className="w-24 h-24 bg-gradient-to-br from-blue-100 via-purple-100 to-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-8 shadow-lg">
                <MessageCircle className="w-12 h-12 text-blue-600" />
              </div>
              <h4 className="text-2xl font-bold text-gray-800 mb-4">Start a conversation with Xbot!</h4>
              <p className="text-gray-600 mb-6 text-lg leading-relaxed max-w-md mx-auto">Ask questions, share images, upload documents, or discuss any topic.</p>
              <div className="flex flex-wrap gap-3 justify-center max-w-lg mx-auto">
                <span className="px-4 py-2 bg-blue-100 text-blue-800 text-sm font-semibold rounded-full border border-blue-200">Images</span>
                <span className="px-4 py-2 bg-green-100 text-green-800 text-sm font-semibold rounded-full border border-green-200">Documents</span>
                <span className="px-4 py-2 bg-purple-100 text-purple-800 text-sm font-semibold rounded-full border border-purple-200">Code</span>
                <span className="px-4 py-2 bg-orange-100 text-orange-800 text-sm font-semibold rounded-full border border-orange-200">Analysis</span>
              </div>
            </div>
          )}
          
          {activeConversation.messages.map((msg, idx) => (
            <div key={msg.id || idx} className={`mb-8 flex ${msg.sender === 'User' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex gap-4 max-w-4xl ${msg.sender === 'User' ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <div className={`
                  w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 mt-1 shadow-lg
                  ${msg.sender === 'User' 
                    ? 'bg-gradient-to-br from-green-500 to-emerald-600' 
                    : 'bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600'
                  }
                `}>
                  {msg.sender === 'User' ? (
                    <User className="w-5 h-5 text-white" />
                  ) : (
                    <Bot className="w-5 h-5 text-white" />
                  )}
                </div>

                {/* Message Content */}
                <div className={`
                  px-5 py-4 rounded-2xl shadow-lg border backdrop-blur-sm flex-1 relative group
                  ${msg.sender === 'User' 
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white border-blue-600/20' 
                    : 'bg-white/90 text-gray-800 border-gray-200/50'
                  }
                  ${msg.sender === 'User' ? 'rounded-tr-lg' : 'rounded-tl-lg'}
                `}>
                  
                  {/* Action buttons */}
                  <div className={`absolute top-2 ${
                    msg.sender === 'User' ? 'left-2' : 'right-2'
                  } flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200`}>
                    
                    {/* User edit navigation */}
                    {msg.sender === 'User' && msg.branches && msg.branches.length > 1 && !msg.isEditing && !isLoading && (
                      <div className="flex items-center gap-1 bg-white/90 rounded-lg p-1 shadow-sm border border-gray-200 mr-1">
                        <button
                          onClick={() => handleNavigateUserEdit(msg.id, 'prev')}
                          disabled={(msg.currentBranchIndex ?? 0) === 0}
                          className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          title="Previous branch"
                        >
                          <ChevronLeft className="w-4 h-4 text-gray-600" />
                        </button>

                        <span className="text-xs text-gray-500 px-2 font-medium">
                          {(msg.currentBranchIndex ?? 0) + 1} / {msg.branches.length}
                        </span>

                        <button
                          onClick={() => handleNavigateUserEdit(msg.id, 'next')}
                          disabled={(msg.currentBranchIndex ?? 0) === msg.branches.length - 1}
                          className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          title="Next branch"
                        >
                          <ChevronRight className="w-4 h-4 text-gray-600" />
                        </button> 
                      </div>
                    )}

                    {/* Bot message navigation and regenerate buttons */}
                    {msg.sender === 'Bot' && !msg.isStreaming && !isLoading && (
                      <>
                        {msg.responses && msg.responses.length > 1 && (
                          <div className="flex items-center gap-1 bg-white/90 rounded-lg p-1 shadow-sm border border-gray-200">
                            <button
                              onClick={() => handleNavigateResponse(msg.id, 'prev')}
                              disabled={(msg.currentResponseIndex || 0) === 0}
                              className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                              title="Previous response"
                            >
                              <ChevronLeft className="w-4 h-4 text-gray-600" />
                            </button>
                            
                            <span className="text-xs text-gray-500 px-2 font-medium">
                              {(msg.currentResponseIndex || 0) + 1} / {msg.responses.length}
                            </span>
                            
                            <button
                              onClick={() => handleNavigateResponse(msg.id, 'next')}
                              disabled={(msg.currentResponseIndex || 0) === (msg.responses?.length || 1) - 1}
                              className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                              title="Next response"
                            >
                              <ChevronRight className="w-4 h-4 text-gray-600" />
                            </button>
                          </div>
                        )}
                        
                        <button
                          onClick={() => handleRegenerateResponse(msg.id)}
                          className="p-1.5 bg-white/90 hover:bg-gray-100 rounded-lg shadow-sm border border-gray-200 transition-all duration-200"
                          title="Regenerate response"
                        >
                          <RotateCcw className="w-4 h-4 text-gray-600" />
                        </button>
                      </>
                    )}
                    
                    {/* User message edit button */}
                    {msg.sender === 'User' && !msg.isEditing && !isLoading && (
                      <button
                        onClick={() => dispatch(toggleMessageEdit(msg.id))}
                        className="p-1.5 text-white/70 hover:text-white hover:bg-white/20 rounded-lg transition-all duration-200"
                        title="Edit message"
                      >
                        <Edit3 size={14} />
                      </button>
                    )}
                  </div>
                  
                  {/* Message content rendering */}
                  {msg.isEditing ? (
                    <EditableMessage
                      msg={msg}
                      onSave={(newText) => {
                        dispatch(regenerateFromMessage({
                          messageId: msg.id,
                          newText,
                          files: msg.files || []
                        }));
                      }}
                      onCancel={() => dispatch(toggleMessageEdit(msg.id))}
                    />
                  ) : (
                    <>
                      {msg.text && (
                        <div className="mb-3 last:mb-0">
                          {msg.sender === 'User' ? (
                            <div className="whitespace-pre-wrap leading-relaxed text-[15px]">{msg.text}</div>
                          ) : (
                            <div className="prose prose-sm max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                              {/* ✅ FIXED ReactMarkdown with enhanced image component */}
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                rehypePlugins={[rehypeHighlight, rehypeStripHljs]}
                                components={{
                                  code: ({ inline, className, children, ...props }) => {
                                    const text = String(children).replace(/\n$/, '')
                                    const hasLang = Boolean(className)
                                    const isSingleLine = !text.includes('\n')

                                    if (inline) {
                                      return <InlineCode {...props}>{children}</InlineCode>
                                    }

                                    if (isSingleLine && !hasLang) {
                                      return <InlineCode {...props}>{children}</InlineCode>
                                    }

                                    return <CodeBlock className={className} {...props}>{children}</CodeBlock>
                                  },
                                  pre: ({ children }) => <>{children}</>,
                                  p: ({ children, ...props }) => (
                                    <p className="mb-3 last:mb-0 leading-relaxed text-gray-700" {...props}>
                                      {children}
                                    </p>
                                  ),
                                  ul: ({ children, ...props }) => (
                                    <ul className="list-disc ml-5 mb-3 space-y-1" {...props}>
                                      {children}
                                    </ul>
                                  ),
                                  ol: ({ children, ...props }) => (
                                    <ol className="list-decimal ml-5 mb-3 space-y-1" {...props}>
                                      {children}
                                    </ol>
                                  ),
                                  li: ({ children, ...props }) => (
                                    <li className="text-gray-700 leading-relaxed" {...props}>
                                      {children}
                                    </li>
                                  ),
                                  blockquote: ({ children, ...props }) => (
                                    <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-3 bg-gray-50 py-2 rounded-r" {...props}>
                                      {children}
                                    </blockquote>
                                  ),
                                  h1: ({ children, ...props }) => (
                                    <h1 className="text-xl font-bold mb-3 text-gray-800 border-b border-gray-200 pb-1" {...props}>
                                      {children}
                                    </h1>
                                  ),
                                  h2: ({ children, ...props }) => (
                                    <h2 className="text-lg font-bold mb-2 text-gray-800" {...props}>
                                      {children}
                                    </h2>
                                  ),
                                  h3: ({ children, ...props }) => (
                                    <h3 className="text-base font-semibold mb-2 text-gray-800" {...props}>
                                      {children}
                                    </h3>
                                  ),
                                  h4: ({ children, ...props }) => (
                                    <h4 className="text-sm font-semibold mb-1 text-gray-800" {...props}>
                                      {children}
                                    </h4>
                                  ),
                                  strong: ({ children, ...props }) => (
                                    <strong className="font-semibold text-gray-800" {...props}>
                                      {children}
                                    </strong>
                                  ),
                                  em: ({ children, ...props }) => (
                                    <em className="italic text-gray-700" {...props}>
                                      {children}
                                    </em>
                                  ),
                                  table: ({ children, ...props }) => (
                                    <div className="overflow-x-auto my-3">
                                      <table className="min-w-full border border-gray-300 rounded overflow-hidden text-sm" {...props}>
                                        {children}
                                      </table>
                                    </div>
                                  ),
                                  thead: ({ children, ...props }) => (
                                    <thead className="bg-gray-100" {...props}>
                                      {children}
                                    </thead>
                                  ),
                                  tbody: ({ children, ...props }) => (
                                    <tbody className="bg-white" {...props}>
                                      {children}
                                    </tbody>
                                  ),
                                  tr: ({ children, ...props }) => (
                                    <tr className="border-b border-gray-200" {...props}>
                                      {children}
                                    </tr>
                                  ),
                                  th: ({ children, ...props }) => (
                                    <th className="px-3 py-2 text-left font-semibold text-gray-800 border-r border-gray-200 last:border-r-0" {...props}>
                                      {children}
                                    </th>
                                  ),
                                  td: ({ children, ...props }) => (
                                    <td className="px-3 py-2 text-gray-700 border-r border-gray-200 last:border-r-0" {...props}>
                                      {children}
                                    </td>
                                  ),
                                  a: ({ href, children, ...props }) => (
                                    <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 underline" {...props}>
                                      {children}
                                    </a>
                                  ),
                                  // ✅ BULLETPROOF Image Component with comprehensive validation
                                  img: ({ src, alt, ...props }) => {
                                    console.log('🖼️ ReactMarkdown img render:', { 
                                      src: src,
                                      srcType: typeof src,
                                      srcLength: src?.length,
                                      alt,
                                      srcPreview: src?.substring?.(0, 100)
                                    });
                                    
                                    // Comprehensive validation
                                    const cleanSrc = typeof src === 'string' ? src.trim() : '';
const isInvalidSrc =
  !cleanSrc ||
  cleanSrc === 'undefined' ||
  cleanSrc === 'null' ||
  !(
    cleanSrc.startsWith('data:image/') ||        // Accept data URLs
    cleanSrc.startsWith('http://') ||
    cleanSrc.startsWith('https://')
  );


                                    if (isInvalidSrc) {
                                      console.error('❌ Invalid src detected:', { src, alt, srcType: typeof src });
                                      return (
                                        <div className="my-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                                          <div className="text-red-600 font-medium mb-2">❌ Invalid image source</div>
                                          <div className="text-xs text-gray-600 space-y-1">
                                            <div><strong>Source:</strong> {String(src)}</div>
                                            <div><strong>Type:</strong> {typeof src}</div>
                                            <div><strong>Alt:</strong> {alt || 'none'}</div>
                                          </div>
                                          <button 
                                            onClick={() => {
                                              console.log('Full debug:', { src, alt, props });
                                              alert(`Debug info logged to console`);
                                            }}
                                            className="mt-2 px-2 py-1 bg-red-500 text-white text-xs rounded"
                                          >
                                            Debug Console
                                          </button>
                                        </div>
                                      );
                                    }

                                    // const cleanSrc = src.trim();

                                    let imgUrl = generatedImageUrl;
  if (imageHistory.length > 0 && currentImageIndex !== null) {
    imgUrl = imageHistory[currentImageIndex]?.url;
  }

                                    return (
                                      <div className="my-4 text-center">
                                        <img
                                          src={imgUrl}
                                          alt={alt || 'Generated image'}
                                          {...props}
                                          className="max-w-full h-auto rounded-lg shadow-lg mx-auto cursor-pointer hover:shadow-xl transition-all duration-200 hover:scale-[1.02]"
                                          style={{ 
                                            maxHeight: '500px', 
                                            objectFit: 'contain',
                                            backgroundColor: '#f9fafb'
                                          }}
                                          onLoad={() => console.log('✅ Image loaded:', cleanSrc.substring(0, 50))}
                                          onError={(e) => {
                                            console.error('❌ Image load error:', {
                                              src: cleanSrc.substring(0, 50),
                                              originalSrc: src,
                                              isDataUrl: cleanSrc.startsWith('data:'),
                                              length: cleanSrc.length
                                            });
                                            
                                            const target = e.target as HTMLImageElement;
                                            target.style.display = 'none';
                                            
                                            const errorDiv = document.createElement('div');
                                            errorDiv.className = 'bg-red-50 border border-red-200 rounded-lg p-4 text-center text-red-600 my-4';
                                            errorDiv.innerHTML = `
                                              <div class="font-medium mb-2">Failed to load image</div>
                                              <div class="text-xs text-gray-500 break-all mb-2">
                                                ${cleanSrc.length > 100 ? cleanSrc.substring(0, 100) + '...' : cleanSrc}
                                              </div>
                                              <div class="text-xs">
                                                <strong>Length:</strong> ${cleanSrc.length} | 
                                                <strong>Type:</strong> ${cleanSrc.startsWith('data:') ? 'Data URL' : 'Regular URL'}
                                              </div>
                                            `;
                                            
                                            target.parentNode?.insertBefore(errorDiv, target.nextSibling);
                                          }}
                                          onClick={() => window.open(cleanSrc, '_blank')}
                                          loading="lazy"
                                          referrerPolicy="no-referrer"
                                          crossOrigin="anonymous"
                                        />
                                        
                                        {alt && alt !== 'Generated image' && (
                                          <p className="text-sm text-gray-500 mt-2 italic px-4">
                                            {alt}
                                          </p>
                                        )}
                                        
                                        <p className="text-xs text-gray-400 mt-1 opacity-0 hover:opacity-100 transition-opacity">
                                          Click to view full size
                                        </p>
                                      </div>
                                    );
                                  },
                                }}
                              >
                                {msg.text}
                              </ReactMarkdown>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {msg.files && msg.files.length > 0 && (
                        <div className="mt-4">
                          {msg.files.map((file, fileIndex) => renderFilePreview(file, fileIndex, true))}
                        </div>
                      )}
                      
                      {msg.isStreaming && (
                        <span className="inline-block w-0.5 h-5 bg-current ml-1 animate-pulse rounded-full"></span>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* File Preview Area */}
      {selectedFiles.length > 0 && (
        <div className="bg-white/95 backdrop-blur-sm border-t border-gray-200 shadow-lg">
          <div className="max-w-4xl mx-auto px-6 py-4">
            <div className="flex items-center gap-3 text-sm text-gray-600 mb-4">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <Paperclip className="w-4 h-4 text-blue-600" />
              </div>
              <span className="font-semibold">Selected files ({selectedFiles.length}):</span>
            </div>
            <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto custom-scrollbar">
              {selectedFiles.map((file, index) => renderFilePreview(file, index, false))}
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50/95 backdrop-blur-sm border-t border-red-200">
          <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-3 text-red-800">
            <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-4 h-4 text-red-600" />
            </div>
            <span className="text-sm font-medium"><strong>Error:</strong> {error}</span>
          </div>
        </div>
      )}

      {/* Enhanced Input Area */}
      <div className="bg-white/95 backdrop-blur-sm border-t border-gray-200 shadow-lg">
        <div className="max-w-4xl mx-auto px-6 py-5">
          <div className="flex items-end gap-4">
            {/* File Upload Button */}
            <div className="flex-shrink-0">
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
                className="w-11 h-11 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 text-gray-600 hover:text-gray-700 disabled:text-gray-400 rounded-xl transition-all duration-200 disabled:cursor-not-allowed flex items-center justify-center shadow-sm hover:shadow-md border border-gray-200 hover:border-gray-300"
                title="Upload files (images, documents, etc.)"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>
            
            {/* Message Input Container */}
            <div className="flex-1 relative">
              <div className="relative flex">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => dispatch(setInput(e.target.value))}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your message... (Shift+Enter for new line)"
                  disabled={isLoading}
                  className="w-full px-5 py-3.5 pr-14 border border-gray-300 rounded-2xl resize-none outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 min-h-[52px] max-h-36 disabled:opacity-50 disabled:cursor-not-allowed text-gray-800 placeholder-gray-500 text-[15px] leading-relaxed shadow-sm hover:shadow-md focus:shadow-lg bg-white custom-scrollbar"
                  rows={1}
                  style={{ paddingRight: '60px' }}
                />
                
                {(input.length > 0 || selectedFiles.length > 0) && (
                  <div className="absolute bottom-2 right-16 flex items-center gap-2">
                    {selectedFiles.length > 0 && (
                      <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full font-medium">
                        {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}
                      </span>
                    )}
                    {input.length > 100 && (
                      <span className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded-full">
                        {input.length}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Tool Selection */}
            <div className="mb-2 flex items-center space-x-2 text-sm">
              {['chat','search','image'].map(tool => (
                <button
                  key={tool}
                  onClick={() => setActiveTool(tool as any)}
                  className={`px-2 py-1 rounded-full transition ${
                    activeTool===tool
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {tool === 'chat' ? 'Chat' : tool === 'search' ? 'Search 🔍' : 'Image 🖼️'}
                </button>
              ))}
            </div>

            {/* Send Button */}
            <div className="flex-shrink-0">
              <button
                onClick={() => {
                  if (activeTool === 'search') return handleSearch();
                  if (activeTool === 'image') return handleGenerateImage();
                  return handleSend();
                }}
                disabled={isLoading || (!input.trim() && selectedFiles.length === 0)}
                className="w-11 h-11 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl hover:scale-105 active:scale-95"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
          
          {/* Helper Text */}
          <div className="flex items-center justify-between mt-3 px-1">
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Paperclip className="w-3 h-3" />
                Drag & drop files
              </span>
              <span>Press Shift+Enter for new line</span>
            </div>
            <div className="text-xs text-gray-400">
              {input.length > 0 && `${input.length} characters`}
            </div>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleInputChange}
            className="hidden"
            accept="image/*,.pdf,.doc,.docx,.txt,.json,.csv"
          />
        </div>
      </div>
    </div>
  );
};

export default Chat;
