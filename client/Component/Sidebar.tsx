// Sidebar.tsx - Enhanced sidebar with provider grouping and multi-model support

import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Plus, MessageSquare, ChevronDown, ChevronUp, Bot, Menu, ChevronLeft, Trash2, Eye, FileText } from 'lucide-react';
import { RootState } from '../store';
import { createNewConversation, switchConversation, deleteConversation, setSelectedModel, fetchAvailableModels } from '../chatSlice';
import { getProviderIcon, getProviderColor } from '../utils/modelUtils';
import { useSidebar } from '../contexts/SidebarContext';

const Sidebar = () => {
  const dispatch = useDispatch();
  const { 
    conversations, 
    activeConversationId, 
    selectedModel, 
    availableModels,
    modelsLoading,
    modelsError 
  } = useSelector((state: RootState) => state.chat);
  
  const { isCollapsed, setIsCollapsed, isMobile, setIsMobile } = useSidebar();
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [newChatButtonClicked, setNewChatButtonClicked] = useState(false);

  // Check for mobile device
  useEffect(() => {
    // Skip during SSR
    if (typeof window === 'undefined') return;
    
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      const wasMobile = isMobile;
      setIsMobile(mobile);
      
      // Only auto-collapse when transitioning from desktop to mobile
      if (mobile && !wasMobile && !isCollapsed) {
        setIsCollapsed(true);
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [isMobile, isCollapsed, setIsMobile, setIsCollapsed]);

  // Fetch models on component mount
  useEffect(() => {
    dispatch(fetchAvailableModels() as any);
  }, [dispatch]);

  const handleNewChat = () => {
    const currentConversation = conversations.find(conv => conv.id === activeConversationId);
    
    // Check if current conversation is empty
    if (currentConversation && currentConversation.messages.length === 0) {
      // Provide visual feedback that button was clicked but no new chat created
      setNewChatButtonClicked(true);
      setTimeout(() => setNewChatButtonClicked(false), 300);
      return;
    }
    
    dispatch(createNewConversation());
  };

  // Get tooltip text for new chat button
  const getNewChatTooltip = () => {
    const currentConversation = conversations.find(conv => conv.id === activeConversationId);
    if (currentConversation && currentConversation.messages.length === 0) {
      return "Start a conversation first to create a new chat";
    }
    return "Create new chat";
  };

  const handleConversationClick = (conversationId: string) => {
    dispatch(switchConversation(conversationId));
  };

  const handleDeleteConversation = (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    if (conversations.length > 1) {
      dispatch(deleteConversation(conversationId));
    }
  };

  const handleModelChange = (model: string) => {
    dispatch(setSelectedModel(model));
    setShowModelSelector(false);
  };

  const toggleSidebar = () => {
    setIsAnimating(true);
    setIsCollapsed(!isCollapsed);
    if (!isCollapsed) {
      setShowModelSelector(false);
    }
    // Reset animation state after transition
    setTimeout(() => setIsAnimating(false), 300);
  };

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    // Skip during SSR
    if (typeof document === 'undefined') return;
    
    const handleClickOutside = (event: MouseEvent) => {
      if (isMobile && !isCollapsed) {
        const sidebar = document.querySelector('[data-sidebar]');
        if (sidebar && !sidebar.contains(event.target as Node)) {
          setIsCollapsed(true);
        }
      }
    };

    if (isMobile) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isMobile, isCollapsed]);

  // Group models by provider
  const groupedModels = availableModels.reduce((acc, model) => {
    if (!acc[model.provider]) {
      acc[model.provider] = [];
    }
    acc[model.provider].push(model);
    return acc;
  }, {} as Record<string, typeof availableModels>);

  // Provider icons and colors - moved to utils

  const currentModel = availableModels.find(model => model.name === selectedModel);

  return (
    <>
      {/* Mobile Overlay */}
      {isMobile && !isCollapsed && (
        <div 
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 transition-opacity duration-300 animate-mobile-fade-in"
          onClick={() => setIsCollapsed(true)}
          aria-label="Close sidebar"
        />
      )}
      
      {/* Sidebar */}
      <div 
        data-sidebar
        className={`
          sidebar-bg-gradient sidebar-bg sidebar-border
          backdrop-blur-md border-r
          transition-all duration-300 ease-in-out transform
          ${isCollapsed 
            ? (isMobile 
                ? 'w-0 -translate-x-full opacity-0 pointer-events-none' 
                : 'w-14 sm:w-16 lg:w-18') 
            : 'w-64 sm:w-72 md:w-80 lg:w-84 translate-x-0 opacity-100'} 
          ${isMobile ? 'fixed inset-y-0 left-0 z-50 touch-target mobile-scroll' : 'relative'}
          min-h-screen flex flex-col overflow-hidden
          ${isAnimating ? 'will-change-transform' : ''}
        `}
        style={{
          boxShadow: isCollapsed 
            ? 'var(--sidebar-shadow-collapsed)' 
            : 'var(--sidebar-shadow), var(--sidebar-inset-shadow)'
        }}
      >
      
      {/* Header */}
      <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'} p-2 sm:p-3 md:p-4 border-b sidebar-header-border flex-shrink-0 sidebar-header-bg`}>
        {!isCollapsed && (
          <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 transition-all duration-300">
            <div className="w-7 h-7 sm:w-8 sm:h-8 md:w-9 md:h-9 sidebar-logo-bg rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg sidebar-logo-ring">
              <Bot className="w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 text-white drop-shadow-sm" />
            </div>
            <h1 className="text-base sm:text-lg md:text-xl font-bold sidebar-title-gradient bg-clip-text text-transparent truncate">
              AI Assistant
            </h1>
          </div>
        )}
        
        {/* Enhanced Toggle Button */}
        <button
          onClick={toggleSidebar}
          className={`
            relative p-1.5 sm:p-2 md:p-2.5 rounded-xl transition-all duration-300 ease-out
            ${isCollapsed 
              ? 'sidebar-toggle-collapsed-bg sidebar-toggle-collapsed-hover-bg shadow-lg sidebar-toggle-collapsed-ring' 
              : 'sidebar-toggle-bg sidebar-toggle-hover-bg'
            }
            hover:scale-110 active:scale-95 flex-shrink-0 z-10
            transform hover:rotate-3 active:rotate-0
            group overflow-hidden
          `}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          {isCollapsed ? (
            <Menu className="w-4 h-4 sm:w-5 sm:h-5 text-white relative z-10 transition-transform duration-300 group-hover:scale-110" />
          ) : (
            <ChevronLeft className="w-4 h-4 sm:w-5 sm:h-5 sidebar-toggle-text group-hover:text-slate-800 dark:group-hover:text-white relative z-10 transition-all duration-300 group-hover:scale-110 group-hover:-translate-x-0.5" />
          )}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-2 sm:p-3 md:p-4 flex-shrink-0">
        {isCollapsed ? (
          <div className="flex justify-center">
            <button
              onClick={handleNewChat}
              className={`w-10 h-10 sm:w-11 sm:h-11 md:w-12 md:h-12 sidebar-new-chat-bg sidebar-new-chat-hover-bg text-white rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl transform hover:scale-110 active:scale-95 sidebar-new-chat-ring sidebar-new-chat-hover-ring group relative overflow-hidden ${
                newChatButtonClicked ? 'animate-pulse bg-orange-500' : ''
              }`}
              aria-label={getNewChatTooltip()}
              title={getNewChatTooltip()}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <Plus className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 relative z-10 transition-transform duration-300 group-hover:rotate-90" />
            </button>
          </div>
        ) : (
          <button
            onClick={handleNewChat}
            className={`w-full sidebar-new-chat-bg sidebar-new-chat-hover-bg text-white rounded-xl transition-all duration-300 flex items-center justify-center space-x-1.5 sm:space-x-2 py-2.5 sm:py-3 md:py-3.5 shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98] sidebar-new-chat-ring sidebar-new-chat-hover-ring group relative overflow-hidden ${
              newChatButtonClicked ? 'animate-pulse bg-orange-500' : ''
            }`}
            aria-label={getNewChatTooltip()}
            title={getNewChatTooltip()}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <Plus className="w-4 h-4 sm:w-5 sm:h-5 relative z-10 transition-transform duration-300 group-hover:rotate-90" />
            <span className="font-semibold text-sm sm:text-base relative z-10 new-chat-text">New Chat</span>
          </button>
        )}
      </div>

      {/* Model Selector */}
      {!isCollapsed && (
        <div className="px-2 sm:px-3 md:px-4 pb-2 sm:pb-3 md:pb-4 flex-shrink-0">
          <div className="relative">
            <button
              onClick={() => setShowModelSelector(!showModelSelector)}
              className="w-full sidebar-model-bg sidebar-model-hover-bg sidebar-model-border sidebar-model-hover-border rounded-lg sm:rounded-xl p-2 sm:p-3 text-left flex items-center justify-between transition-all duration-200 hover:shadow-lg group"
              aria-label="Select AI model"
            >
              <div className="flex items-center space-x-1.5 sm:space-x-2 md:space-x-3 min-w-0">
                {currentModel && (
                  <div className={`${getProviderColor(currentModel.provider)} flex-shrink-0`}>
                    {React.createElement(getProviderIcon(currentModel.provider), { className: "w-4 h-4" })}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="text-xs sm:text-sm font-medium text-slate-900 dark:text-white truncate model-name-text">
                    {currentModel?.display_name || selectedModel}
                  </div>
                  {currentModel && (
                    <div className="flex items-center space-x-1 sm:space-x-2 mt-0.5 sm:mt-1">
                      <span className={`text-xs px-1.5 sm:px-2 py-0.5 rounded-full sidebar-model-badge-bg sidebar-model-badge-text sidebar-model-badge-border`}>
                        {currentModel.provider}
                      </span>
                      {currentModel.supports_vision && (
                        <Eye className="w-2.5 h-2.5 sm:w-3 sm:h-3 sidebar-model-vision-text" />
                      )}
                      {currentModel.supports_files && (
                        <FileText className="w-2.5 h-2.5 sm:w-3 sm:h-3 sidebar-model-files-text" />
                      )}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex-shrink-0">
                {showModelSelector ? <ChevronUp className="w-3 h-3 sm:w-4 sm:h-4 transition-transform duration-200 sidebar-toggle-text" /> : <ChevronDown className="w-3 h-3 sm:w-4 sm:h-4 transition-transform duration-200 sidebar-toggle-text" />}
              </div>
            </button>

            {/* Model Dropdown */}
            {showModelSelector && (
              <div className="absolute top-full left-0 right-0 mt-1 sm:mt-2 sidebar-model-dropdown-bg backdrop-blur-sm sidebar-model-dropdown-border rounded-lg sm:rounded-xl sidebar-model-dropdown-shadow z-50 max-h-64 sm:max-h-80 lg:max-h-96 overflow-y-auto custom-scrollbar">
                {modelsLoading ? (
                  <div className="p-3 sm:p-4 text-center sidebar-toggle-text">
                    <div className="animate-spin w-4 h-4 sm:w-5 sm:h-5 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                    <span className="text-xs sm:text-sm">Loading models...</span>
                  </div>
                ) : modelsError ? (
                  <div className="p-3 sm:p-4 text-center text-red-600 dark:text-red-400">
                    <div className="text-xs sm:text-sm">{modelsError}</div>
                    <button 
                      onClick={() => dispatch(fetchAvailableModels() as any)}
                      className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 transition-colors"
                    >
                      Retry
                    </button>
                  </div>
                ) : (
                  Object.entries(groupedModels).map(([provider, models]) => (
                    <div key={provider} className="border-b sidebar-model-section-border last:border-b-0">
                      <div className="px-3 sm:px-4 py-1.5 sm:py-2 sidebar-model-section-header-bg">
                        <div className="flex items-center space-x-1.5 sm:space-x-2">
                          <div className={`${getProviderColor(provider)} flex-shrink-0`}>
                            {React.createElement(getProviderIcon(provider), { className: "w-4 h-4" })}
                          </div>
                          <span className="text-xs sm:text-sm font-medium sidebar-toggle-text capitalize">
                            {provider}
                          </span>
                        </div>
                      </div>
                      {models.map((model) => (
                        <button
                          key={model.name}
                          onClick={() => handleModelChange(model.name)}
                          className={`w-full text-left px-3 sm:px-4 py-2 sm:py-3 sidebar-model-item-hover-bg transition-all duration-150 ${
                            selectedModel === model.name ? 'sidebar-model-item-active-bg sidebar-model-item-active-border' : ''
                          } group`}
                          aria-label={`Select ${model.display_name}`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="text-xs sm:text-sm font-medium text-slate-900 dark:text-white truncate group-hover:text-blue-700 dark:group-hover:text-blue-100 model-dropdown-name">
                                {model.display_name}
                              </div>
                              <div className="text-xs sidebar-toggle-text mt-0.5 sm:mt-1 line-clamp-2 leading-relaxed">
                                {model.description}
                              </div>
                              <div className="flex items-center space-x-1 sm:space-x-2 mt-1 sm:mt-2">
                                {model.supports_vision && (
                                  <span className="text-xs px-1.5 sm:px-2 py-0.5 sidebar-model-vision-bg sidebar-model-vision-text rounded-full flex items-center space-x-0.5 sm:space-x-1 sidebar-model-vision-border">
                                    <Eye className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                                    <span className="hidden sm:inline">Vision</span>
                                  </span>
                                )}
                                {model.supports_files && (
                                  <span className="text-xs px-1.5 sm:px-2 py-0.5 sidebar-model-files-bg sidebar-model-files-text rounded-full flex items-center space-x-0.5 sm:space-x-1 sidebar-model-files-border">
                                    <FileText className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                                    <span className="hidden sm:inline">Files</span>
                                  </span>
                                )}
                              </div>
                            </div>
                            {selectedModel === model.name && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 ring-2 ring-blue-400/30"></div>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto px-2 sm:px-3 md:px-4 space-y-1 sm:space-y-2 custom-scrollbar mobile-scroll min-h-0 py-1 sm:py-2">
        {conversations.length === 0 ? (
          !isCollapsed && (
            <div className="text-center py-8 sm:py-12 sidebar-toggle-text animate-fade-in">
              <div className="relative">
                <MessageSquare className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 opacity-40 animate-pulse" />
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-3 h-3 sidebar-footer-pulse-bg rounded-full animate-ping" />
              </div>
              <p className="text-sm sm:text-base font-medium text-white">No conversations yet</p>
              <p className="text-xs sm:text-sm mt-2 opacity-75 text-gray-200">Start a new chat to begin your AI journey</p>
            </div>
          )
        ) : (
          conversations.map((conversation, index) => (
            <div
              key={conversation.id}
              onClick={() => handleConversationClick(conversation.id)}
              className={`group relative rounded-xl transition-all duration-300 cursor-pointer transform hover:scale-[1.02] ${
                activeConversationId === conversation.id
                  ? 'sidebar-conversation-active-bg sidebar-conversation-active-border sidebar-conversation-active-ring shadow-lg'
                  : 'sidebar-conversation-hover-bg sidebar-conversation-hover-border border border-transparent'
              } ${isCollapsed ? 'p-1.5 sm:p-2 mx-0.5 sm:mx-1' : 'p-2 sm:p-3'}`}
              style={{
                animationDelay: `${index * 50}ms`
              }}
            >
              {isCollapsed ? (
                <div className="flex justify-center">
                  <div className={`${
                    activeConversationId === conversation.id 
                      ? 'sidebar-conversation-icon-active-text sidebar-conversation-icon-active-bg sidebar-conversation-icon-active-ring' 
                      : 'sidebar-toggle-text sidebar-conversation-icon-hover-text sidebar-conversation-icon-hover-bg'
                  } w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8 rounded-lg flex items-center justify-center transition-all duration-300 group-hover:scale-110`}>
                    <MessageSquare className="w-3 h-3 sm:w-4 sm:h-4" />
                  </div>
                </div>
              ) : (
                <div className="flex items-center space-x-2 sm:space-x-3">
                  <div className={`${
                    activeConversationId === conversation.id 
                      ? 'sidebar-conversation-icon-active-text sidebar-conversation-icon-active-bg sidebar-conversation-icon-active-ring' 
                      : 'sidebar-toggle-text sidebar-conversation-icon-hover-text sidebar-conversation-icon-hover-bg'
                  } w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-300`}>
                    <MessageSquare className="w-3 h-3 sm:w-4 sm:h-4" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs sm:text-sm font-semibold truncate transition-all duration-300 conversation-title ${
                      activeConversationId === conversation.id 
                        ? 'text-slate-900 dark:text-white' 
                        : 'text-slate-700 dark:text-gray-200 group-hover:text-slate-900 dark:group-hover:text-white'
                    }`}>
                      {conversation.title}
                    </p>
                    <div className="flex items-center space-x-1 sm:space-x-2 mt-1 sm:mt-1.5">
                      <span className={`text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-lg font-medium transition-all duration-300 ${
                        activeConversationId === conversation.id
                          ? 'sidebar-conversation-badge-active-bg sidebar-conversation-badge-active-text sidebar-conversation-badge-active-border'
                          : 'sidebar-model-badge-bg sidebar-model-badge-text sidebar-model-badge-border sidebar-conversation-badge-hover-bg sidebar-conversation-badge-hover-text sidebar-conversation-badge-hover-border'
                      }`}>
                        {availableModels.find(m => m.name === conversation.model)?.provider || 'unknown'}
                      </span>
                      <p className="text-xs sidebar-toggle-text hidden md:block font-medium">
                        {new Date(conversation.updatedAt).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {!isCollapsed && conversations.length > 1 && (
                <button
                  onClick={(e) => handleDeleteConversation(e, conversation.id)}
                  className="absolute right-1 sm:right-2 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 sm:p-1.5 sidebar-delete-btn-hover-bg sidebar-delete-btn-text sidebar-delete-btn-hover-text rounded-lg transition-all duration-300 hover:scale-110 active:scale-95 ring-0 sidebar-delete-btn-hover-ring"
                  aria-label="Delete conversation"
                >
                  <Trash2 className="w-3 h-3 sm:w-4 sm:h-4" />
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      {!isCollapsed && (
        <div className="p-2 sm:p-3 md:p-4 border-t sidebar-footer-border flex-shrink-0 sidebar-footer-bg">
          <div className="text-xs sidebar-footer-text text-center leading-relaxed">
            <div className="flex items-center justify-center space-x-2 mb-1">
              <div className="w-2 h-2 sidebar-footer-pulse-bg rounded-full animate-pulse"></div>
              <span className="font-medium sidebar-footer-gradient">
                Multi-Model AI Assistant
              </span>
              <div className="w-2 h-2 sidebar-footer-pulse-bg rounded-full animate-pulse" style={{animationDelay: '1s'}}></div>
            </div>
            <span className="text-slate-500 dark:text-slate-500 text-xs">
              Powered by LangChain
            </span>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

export default Sidebar;
