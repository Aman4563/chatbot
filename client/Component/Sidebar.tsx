// Sidebar.tsx - Modern collapsible sidebar matching chat design
import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { 
  Plus, 
  MessageSquare, 
  ChevronDown, 
  ChevronUp, 
  X, 
  Bot, 
  Menu, 
  ChevronLeft,
  Settings,
  Trash2
} from 'lucide-react';
import { RootState } from '../store';
import { 
  createNewConversation, 
  switchConversation, 
  deleteConversation,
  setSelectedModel 
} from '../chatSlice';

const Sidebar = () => {
  const dispatch = useDispatch();
  const { conversations, activeConversationId, selectedModel, availableModels } = useSelector(
    (state: RootState) => state.chat
  );
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

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

  return (
    <div className={`
      ${isCollapsed ? 'w-16' : 'w-80'} 
      bg-white border-r border-gray-200 
      transition-all duration-300 ease-in-out
      flex flex-col h-screen
      shadow-sm
    `}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-800">Xbot</h3>
                <p className="text-xs text-gray-500">AI Assistant</p>
              </div>
            </div>
          )}
          
          <button
            onClick={toggleSidebar}
            className={`
              ${isCollapsed ? 'w-10 h-10 mx-auto' : 'w-8 h-8'}
              bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-800 
              rounded-lg transition-all duration-200 
              flex items-center justify-center
              shadow-sm hover:shadow-md
            `}
          >
            {isCollapsed ? <Menu className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {!isCollapsed ? (
          <>
            {/* Model Selector */}
            <div className="p-4 border-b border-gray-100 bg-gray-50/50">
              <div className="relative">
                <button
                  onClick={() => setShowModelSelector(!showModelSelector)}
                  className="w-full p-3 bg-white border border-gray-200 rounded-xl text-left transition-all duration-200 hover:shadow-md hover:border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg flex items-center justify-center">
                        <Settings className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-800">{selectedModel}</span>
                        <p className="text-xs text-gray-500">AI Model</p>
                      </div>
                    </div>
                    {showModelSelector ? (
                      <ChevronUp className="w-4 h-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-400" />
                    )}
                  </div>
                </button>
                
                {showModelSelector && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-xl shadow-lg z-50 overflow-hidden">
                    <div className="max-h-48 overflow-y-auto custom-scrollbar">
                      {availableModels.map((model, index) => (
                        <button
                          key={model}
                          onClick={() => handleModelChange(model)}
                          className={`
                            w-full p-3 text-left transition-colors duration-150 border-b border-gray-100 last:border-b-0
                            ${model === selectedModel 
                              ? 'bg-blue-50 text-blue-700 font-medium' 
                              : 'text-gray-700 hover:bg-gray-50'
                            }
                          `}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`
                              w-2 h-2 rounded-full 
                              ${model === selectedModel ? 'bg-blue-500' : 'bg-gray-300'}
                            `} />
                            <span className="text-sm">{model}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* New Chat Button */}
              <button 
                onClick={handleNewChat}
                className="w-full mt-4 p-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-105 flex items-center justify-center gap-2 font-medium"
              >
                <Plus className="w-4 h-4" />
                <span>New Chat</span>
              </button>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
              <div className="flex items-center gap-2 mb-4">
                <MessageSquare className="w-4 h-4 text-gray-500" />
                <h4 className="text-sm font-semibold text-gray-600">Recent Chats</h4>
                <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">
                  {conversations.length}
                </span>
              </div>
              
              {conversations.length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                    <MessageSquare className="w-8 h-8 text-gray-400" />
                  </div>
                  <p className="text-sm text-gray-500">No conversations yet</p>
                  <p className="text-xs text-gray-400 mt-1">Start a new chat to begin</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {conversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      onClick={() => handleConversationClick(conversation.id)}
                      className={`
                        group relative p-4 rounded-xl cursor-pointer transition-all duration-200 border
                        ${activeConversationId === conversation.id 
                          ? 'bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200 shadow-sm' 
                          : 'bg-gray-50 hover:bg-gray-100 border-gray-200 hover:border-gray-300'
                        }
                      `}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`
                          w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5
                          ${activeConversationId === conversation.id 
                            ? 'bg-gradient-to-br from-blue-500 to-purple-600' 
                            : 'bg-gray-200 group-hover:bg-gray-300'
                          }
                        `}>
                          <MessageSquare className={`
                            w-4 h-4 
                            ${activeConversationId === conversation.id ? 'text-white' : 'text-gray-600'}
                          `} />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <h5 className={`
                            text-sm font-medium mb-1 truncate
                            ${activeConversationId === conversation.id ? 'text-blue-800' : 'text-gray-800'}
                          `}>
                            {conversation.title}
                          </h5>
                          <div className="flex items-center justify-between text-xs">
                            <span className={`
                              ${activeConversationId === conversation.id ? 'text-blue-600' : 'text-gray-500'}
                            `}>
                              {conversation.messages.length} message{conversation.messages.length !== 1 ? 's' : ''}
                            </span>
                            <span className={`
                              px-2 py-1 rounded-full text-xs font-medium
                              ${activeConversationId === conversation.id 
                                ? 'bg-blue-100 text-blue-700' 
                                : 'bg-gray-200 text-gray-600'
                              }
                            `}>
                              {conversation.model}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      {conversations.length > 1 && (
                        <button
                          onClick={(e) => handleDeleteConversation(e, conversation.id)}
                          className="absolute top-3 right-3 w-6 h-6 bg-red-100 hover:bg-red-200 text-red-600 hover:text-red-700 rounded-lg transition-all duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100 shadow-sm"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          /* Collapsed Sidebar */
          <div className="flex-1 overflow-y-auto p-2">
            {/* Collapsed New Chat Button */}
            <button 
              onClick={handleNewChat}
              className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl transition-all duration-200 shadow-md hover:shadow-lg flex items-center justify-center mb-4 mx-auto"
              title="New Chat"
            >
              <Plus className="w-5 h-5" />
            </button>

            {/* Collapsed Conversations */}
            <div className="space-y-2">
              {conversations.slice(0, 8).map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => handleConversationClick(conversation.id)}
                  className={`
                    w-12 h-12 rounded-xl transition-all duration-200 flex items-center justify-center mx-auto
                    ${activeConversationId === conversation.id 
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-md' 
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-800'
                    }
                  `}
                  title={conversation.title}
                >
                  <MessageSquare className="w-4 h-4" />
                </button>
              ))}
              
              {conversations.length > 8 && (
                <div className="w-12 h-8 bg-gray-100 rounded-lg flex items-center justify-center mx-auto">
                  <span className="text-xs text-gray-500">+{conversations.length - 8}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
