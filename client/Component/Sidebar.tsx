// Sidebar.tsx - Enhanced sidebar with provider grouping and multi-model support

import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Plus, MessageSquare, ChevronDown, ChevronUp, X, Bot, Menu, ChevronLeft, Settings, Trash2, Eye, FileText, Zap, Brain } from 'lucide-react';
import { RootState } from '../store';
import { createNewConversation, switchConversation, deleteConversation, setSelectedModel, fetchAvailableModels } from '../chatSlice';

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
  
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Fetch models on component mount
  useEffect(() => {
    dispatch(fetchAvailableModels());
  }, [dispatch]);

  const handleNewChat = () => {
    dispatch(createNewConversation());
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
    setIsCollapsed(!isCollapsed);
    if (!isCollapsed) {
      setShowModelSelector(false);
    }
  };

  // Group models by provider
  const groupedModels = availableModels.reduce((acc, model) => {
    if (!acc[model.provider]) {
      acc[model.provider] = [];
    }
    acc[model.provider].push(model);
    return acc;
  }, {} as Record<string, typeof availableModels>);

  // Provider icons and colors
  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'mistral':
        return <Zap className="w-4 h-4" />;
      case 'openai':
        return <Brain className="w-4 h-4" />;
      case 'anthropic':
        return <Bot className="w-4 h-4" />;
      case 'google':
        return <Eye className="w-4 h-4" />;
      default:
        return <Bot className="w-4 h-4" />;
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider) {
      case 'mistral':
        return 'text-orange-500';
      case 'openai':
        return 'text-green-500';
      case 'anthropic':
        return 'text-purple-500';
      case 'google':
        return 'text-blue-500';
      default:
        return 'text-gray-500';
    }
  };

  const currentModel = availableModels.find(model => model.name === selectedModel);

  return (
    <div className={`bg-gradient-to-b from-slate-900 to-slate-800 text-white transition-all duration-300 ease-in-out ${
      isCollapsed ? 'w-16' : 'w-80'
    } min-h-screen border-r border-slate-700/50 shadow-2xl`}>
      
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
        {!isCollapsed && (
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              AI Assistant
            </h1>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
        >
          {isCollapsed ? <Menu className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={handleNewChat}
          className={`${
            isCollapsed ? 'w-10 h-10' : 'w-full'
          } bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98] ${
            isCollapsed ? '' : 'py-3'
          }`}
        >
          <Plus className={`${isCollapsed ? 'w-5 h-5' : 'w-5 h-5'}`} />
          {!isCollapsed && <span className="font-medium">New Chat</span>}
        </button>
      </div>

      {/* Model Selector */}
      {!isCollapsed && (
        <div className="px-4 pb-4">
          <div className="relative">
            <button
              onClick={() => setShowModelSelector(!showModelSelector)}
              className="w-full bg-slate-800/80 hover:bg-slate-700/80 border border-slate-600/50 rounded-xl p-3 text-left flex items-center justify-between transition-all duration-200 hover:border-slate-500/50"
            >
              <div className="flex items-center space-x-3">
                {currentModel && (
                  <div className={`${getProviderColor(currentModel.provider)}`}>
                    {getProviderIcon(currentModel.provider)}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">
                    {currentModel?.display_name || selectedModel}
                  </div>
                  {currentModel && (
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getProviderColor(currentModel.provider)} bg-opacity-20`}>
                        {currentModel.provider}
                      </span>
                      {currentModel.supports_vision && (
                        <Eye className="w-3 h-3 text-blue-400" title="Vision capable" />
                      )}
                      {currentModel.supports_files && (
                        <FileText className="w-3 h-3 text-green-400" title="File analysis" />
                      )}
                    </div>
                  )}
                </div>
              </div>
              {showModelSelector ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {/* Model Dropdown */}
            {showModelSelector && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-slate-600/50 rounded-xl shadow-2xl z-50 max-h-96 overflow-y-auto">
                {modelsLoading ? (
                  <div className="p-4 text-center text-slate-400">
                    <div className="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                    Loading models...
                  </div>
                ) : modelsError ? (
                  <div className="p-4 text-center text-red-400">
                    <div className="text-sm">{modelsError}</div>
                    <button 
                      onClick={() => dispatch(fetchAvailableModels())}
                      className="mt-2 text-xs text-blue-400 hover:text-blue-300"
                    >
                      Retry
                    </button>
                  </div>
                ) : (
                  Object.entries(groupedModels).map(([provider, models]) => (
                    <div key={provider} className="border-b border-slate-700/50 last:border-b-0">
                      <div className="px-4 py-2 bg-slate-700/30">
                        <div className="flex items-center space-x-2">
                          <div className={getProviderColor(provider)}>
                            {getProviderIcon(provider)}
                          </div>
                          <span className="text-sm font-medium text-slate-300 capitalize">
                            {provider}
                          </span>
                        </div>
                      </div>
                      {models.map((model) => (
                        <button
                          key={model.name}
                          onClick={() => handleModelChange(model.name)}
                          className={`w-full text-left px-4 py-3 hover:bg-slate-700/50 transition-colors ${
                            selectedModel === model.name ? 'bg-slate-700/70' : ''
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-white truncate">
                                {model.display_name}
                              </div>
                              <div className="text-xs text-slate-400 mt-1 line-clamp-2">
                                {model.description}
                              </div>
                              <div className="flex items-center space-x-2 mt-2">
                                {model.supports_vision && (
                                  <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded-full flex items-center space-x-1">
                                    <Eye className="w-3 h-3" />
                                    <span>Vision</span>
                                  </span>
                                )}
                                {model.supports_files && (
                                  <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded-full flex items-center space-x-1">
                                    <FileText className="w-3 h-3" />
                                    <span>Files</span>
                                  </span>
                                )}
                              </div>
                            </div>
                            {selectedModel === model.name && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
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
      <div className="flex-1 overflow-y-auto px-4 space-y-2">
        {conversations.length === 0 ? (
          !isCollapsed && (
            <div className="text-center py-8 text-slate-400">
              <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">No conversations yet</p>
              <p className="text-xs mt-1">Start a new chat to begin</p>
            </div>
          )
        ) : (
          conversations.map((conversation) => (
            <div
              key={conversation.id}
              onClick={() => handleConversationClick(conversation.id)}
              className={`group relative rounded-xl transition-all duration-200 cursor-pointer ${
                activeConversationId === conversation.id
                  ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30'
                  : 'hover:bg-slate-700/30'
              } ${isCollapsed ? 'p-2' : 'p-3'}`}
            >
              <div className="flex items-center space-x-3">
                <div className={`${
                  activeConversationId === conversation.id 
                    ? 'text-blue-400' 
                    : 'text-slate-400 group-hover:text-slate-300'
                } flex-shrink-0`}>
                  <MessageSquare className={`${isCollapsed ? 'w-5 h-5' : 'w-4 h-4'}`} />
                </div>
                
                {!isCollapsed && (
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${
                      activeConversationId === conversation.id 
                        ? 'text-white' 
                        : 'text-slate-300 group-hover:text-white'
                    }`}>
                      {conversation.title}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        activeConversationId === conversation.id
                          ? 'bg-blue-500/20 text-blue-300'
                          : 'bg-slate-700/50 text-slate-400'
                      }`}>
                        {availableModels.find(m => m.name === conversation.model)?.provider || 'unknown'}
                      </span>
                      <p className="text-xs text-slate-500">
                        {new Date(conversation.updatedAt).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {!isCollapsed && conversations.length > 1 && (
                <button
                  onClick={(e) => handleDeleteConversation(e, conversation.id)}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 text-red-400 hover:text-red-300 rounded transition-all duration-200"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      {!isCollapsed && (
        <div className="p-4 border-t border-slate-700/50">
          <div className="text-xs text-slate-500 text-center">
            Multi-Model AI Assistant
            <br />
            Powered by LangChain
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;
