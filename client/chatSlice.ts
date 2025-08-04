// chatSlice.ts - Complete updated version with all fixes

import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export type FileData = {
  data: string;
  mime_type: string;
  filename: string;
  url?: string;
};

export type Message = {
  id: string;
  sender: 'User' | 'Bot';
  text: string;
  files?: FileData[];
  isStreaming?: boolean;
  timestamp: string;
  isEditing?: boolean;
  responses?: string[];
  currentResponseIndex?: number;
  edits?: string[];
  currentEditIndex?: number;
  branches?: Message[][];
  currentBranchIndex?: number;
};

export type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  model: string;
  createdAt: string;
  updatedAt: string;
};

export type ModelInfo = {
  name: string;
  display_name: string;
  description: string;
  supports_vision: boolean;
  supports_files: boolean;
  provider: string;
};

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  input: string;
  isLoading: boolean;
  error: string | null;
  streamingMessageIndex: number | null;
  selectedModel: string;
  availableModels: ModelInfo[];
  modelsLoading: boolean;
  modelsError: string | null;
  searchResults: string[];
  searchLoading: boolean;
  searchError: string | null;
  generatedImageUrl: string | null;
  imageLoading: boolean;
  imageError: string | null;
  // Enhanced image handling fields
  imageHistory: Array<{ prompt: string; url: string; timestamp: string }>;
  currentImageIndex: number | null;
  // Tool state management
  activeTool: 'chat' | 'search' | 'image';
}

const initialState: ChatState = {
  conversations: [],
  activeConversationId: null,
  input: '',
  isLoading: false,
  error: null,
  streamingMessageIndex: null,
  selectedModel: 'mistral-large',
  availableModels: [],
  modelsLoading: false,
  modelsError: null,
  searchResults: [],
  searchLoading: false,
  searchError: null,
  generatedImageUrl: null,
  imageLoading: false,
  imageError: null,
  imageHistory: [],
  currentImageIndex: null,
  activeTool: 'chat',
};

const generateId = () => Date.now().toString() + Math.random().toString(36).substr(2, 9);

const formatHistoryForAPI = (messages: Message[]) => {
  return messages.map(msg => ({
    role: msg.sender === 'User' ? 'user' : 'assistant',
    content: msg.text,
    files: msg.files || []
  }));
};

// Enhanced web search thunk with better error handling
export const webSearch = createAsyncThunk<
  string[],
  { query: string; num_results?: number },
  { rejectValue: string }
>(
  'chat/webSearch',
  async ({ query, num_results = 5 }, { rejectWithValue }) => {
    try {
      console.log('Starting web search for:', query);
      
      const res = await fetch(
        `${API_BASE}/tools/search?q=${encodeURIComponent(query)}&num_results=${num_results}`
      );
      
      if (!res.ok) {
        const text = await res.text();
        console.error('Search API error:', text);
        return rejectWithValue(text || 'Search failed');
      }
      
      const json = await res.json();
      console.log('Search results:', json);
      return json.results;
    } catch (err: any) {
      console.error('Search network error:', err);
      return rejectWithValue(err.message ?? 'Network error');
    }
  }
);

// Enhanced image generation thunk with better debugging and integration
export const generateImage = createAsyncThunk<
  string,
  { prompt: string },
  { rejectValue: string }
>(
  'chat/generateImage',
  async ({ prompt }, { rejectWithValue }) => {
    try {
      console.log('🖼️ Starting image generation for prompt:', prompt);
      
      const res = await fetch(`${API_BASE}/tools/image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });

      console.log('🔄 Image generation response status:', res.status);

      if (!res.ok) {
        const text = await res.text();
        console.error('❌ Image generation API error:', res.status, text);
        return rejectWithValue(text || 'Image generation failed');
      }
      
      const json = await res.json();
      console.log('📊 Raw backend response:', json);
      
      // ✅ ENHANCED VALIDATION
      if (!json || typeof json !== 'object') {
        console.error('❌ Invalid JSON response:', json);
        return rejectWithValue('Invalid response format');
      }

      if (!json.url) {
        console.error('❌ No URL in response:', json);
        return rejectWithValue('No image URL received from backend');
      }

      if (typeof json.url !== 'string') {
        console.error('❌ URL is not a string:', typeof json.url, json.url);
        return rejectWithValue('Invalid URL type received');
      }

      const trimmedUrl = json.url.trim();
      if (trimmedUrl === '' || trimmedUrl === 'undefined' || trimmedUrl === 'null') {
        console.error('❌ Empty or invalid URL:', json.url);
        return rejectWithValue('Empty or invalid URL received');
      }

      console.log('✅ Valid URL received:', trimmedUrl.substring(0, 100));
      return trimmedUrl;
      
    } catch (err: any) {
      console.error('🚨 Image generation network error:', err);
      return rejectWithValue(err.message ?? 'Network error');
    }
  }
);


export const fetchAvailableModels = createAsyncThunk(
  'chat/fetchAvailableModels',
  async () => {
    const response = await fetch(`${API_BASE}/models`);
    if (!response.ok) {
      throw new Error('Failed to fetch models');
    }
    const models: ModelInfo[] = await response.json();
    return models;
  }
);

export const sendChatMessageStream = createAsyncThunk(
  'chat/sendMessageStream',
  async ({ message, files = [] }: { message: string; files?: FileData[] }, { dispatch, getState }) => {
    const state = getState() as { chat: ChatState };
    const { activeConversationId, selectedModel, conversations } = state.chat;

    if (!activeConversationId) {
      throw new Error('No active conversation');
    }

    const currentConversation = conversations.find(conv => conv.id === activeConversationId);
    const history = currentConversation ? formatHistoryForAPI(currentConversation.messages) : [];

    console.log('Sending chat message:', { message, files, selectedModel, history });

    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: {
          text: message,
          files: files
        },
        history: history,
        system_prompt: "You are a helpful AI assistant with vision and document analysis capabilities. When analyzing images, describe what you see in detail. When analyzing documents, provide summaries and key insights.",
        model_name: selectedModel
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    dispatch(addBotMessage(''));

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (reader) {
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.chunk) {
                dispatch(appendToLastBotMessage(data.chunk));
              } else if (data.done) {
                dispatch(finishStreaming());
                return 'Streaming completed';
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    }

    dispatch(finishStreaming());
    return 'Streaming completed';
  }
);

export const regenerateFromMessage = createAsyncThunk(
  'chat/regenerateFromMessage',
  async ({ messageId, newText, files = [] }: { messageId: string; newText: string; files?: FileData[] }, { dispatch, getState }) => {
    const state = getState() as { chat: ChatState };
    const { activeConversationId, selectedModel, conversations } = state.chat;

    if (!activeConversationId) {
      throw new Error('No active conversation');
    }

    const currentConversation = conversations.find(conv => conv.id === activeConversationId);
    if (!currentConversation) {
      throw new Error('Conversation not found');
    }

    const messageIndex = currentConversation.messages.findIndex(msg => msg.id === messageId);
    if (messageIndex === -1) {
      throw new Error('Message not found');
    }

    const historyMessages = currentConversation.messages.slice(0, messageIndex);
    const history = formatHistoryForAPI(historyMessages);

    dispatch(updateMessageAndTruncate({ messageId, newText, files }));

    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: {
          text: newText,
          files: files
        },
        history: history,
        system_prompt: "You are a helpful AI assistant with vision and document analysis capabilities. When analyzing images, describe what you see in detail. When analyzing documents, provide summaries and key insights.",
        model_name: selectedModel
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to regenerate response');
    }

    dispatch(addBotMessage(''));

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (reader) {
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.chunk) {
                dispatch(appendToLastBotMessage(data.chunk));
              } else if (data.done) {
                dispatch(finishStreaming());
                return 'Regeneration completed';
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    }

    dispatch(finishStreaming());
    return 'Regeneration completed';
  }
);

export const regenerateResponse = createAsyncThunk(
  'chat/regenerateResponse',
  async (messageId: string, { dispatch, getState }) => {
    const state = getState() as { chat: ChatState };
    const { activeConversationId, selectedModel, conversations } = state.chat;

    if (!activeConversationId) {
      throw new Error('No active conversation');
    }

    const currentConversation = conversations.find(conv => conv.id === activeConversationId);
    if (!currentConversation) {
      throw new Error('Conversation not found');
    }

    const messageIndex = currentConversation.messages.findIndex(msg => msg.id === messageId);
    if (messageIndex === -1) {
      throw new Error('Message not found');
    }

    const userMessage = messageIndex > 0 ? currentConversation.messages[messageIndex - 1] : null;
    if (!userMessage || userMessage.sender !== 'User') {
      throw new Error('No user message found to regenerate from');
    }

    const historyMessages = currentConversation.messages.slice(0, messageIndex - 1);
    const history = formatHistoryForAPI(historyMessages);

    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: {
          text: userMessage.text,
          files: userMessage.files || []
        },
        history: history,
        system_prompt: "You are a helpful AI assistant with vision and document analysis capabilities. When analyzing images, describe what you see in detail. When analyzing documents, provide summaries and key insights.",
        model_name: selectedModel
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to regenerate response');
    }

    let newResponseText = '';
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (reader) {
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.chunk) {
                newResponseText += data.chunk;
              } else if (data.done) {
                dispatch(addResponseVersion({ messageId, newResponse: newResponseText }));
                return 'Regeneration completed';
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    }

    dispatch(addResponseVersion({ messageId, newResponse: newResponseText }));
    return 'Regeneration completed';
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setInput: (state, action: PayloadAction<string>) => {
      state.input = action.payload;
    },
    setSelectedModel: (state, action: PayloadAction<string>) => {
      state.selectedModel = action.payload;
      if (state.activeConversationId) {
        const conversation = state.conversations.find(conv => conv.id === state.activeConversationId);
        if (conversation) {
          conversation.model = action.payload;
        }
      }
    },
    setActiveTool: (state, action: PayloadAction<'chat' | 'search' | 'image'>) => {
      state.activeTool = action.payload;
      // Clear tool-specific state when switching tools
      if (action.payload !== 'search') {
        state.searchResults = [];
        state.searchError = null;
      }
      if (action.payload !== 'image') {
        state.generatedImageUrl = null;
        state.imageError = null;
      }
    },
    createNewConversation: (state) => {
      const newConversation: Conversation = {
        id: generateId(),
        title: 'New Chat',
        messages: [],
        model: state.selectedModel,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      state.conversations.unshift(newConversation);
      state.activeConversationId = newConversation.id;
      // Clear tool states when starting new conversation
      state.generatedImageUrl = null;
      state.imageError = null;
      state.searchResults = [];
      state.searchError = null;
      state.activeTool = 'chat';
    },
    switchConversation: (state, action: PayloadAction<string>) => {
      state.activeConversationId = action.payload;
      state.streamingMessageIndex = null;
      const conversation = state.conversations.find(conv => conv.id === action.payload);
      if (conversation) {
        state.selectedModel = conversation.model;
      }
      // Clear tool states when switching conversations
      state.generatedImageUrl = null;
      state.imageError = null;
      state.searchResults = [];
      state.searchError = null;
      state.activeTool = 'chat';
    },
    setUserBranchIndex: (
      state,
      action: PayloadAction<{ messageId: string; branchIndex: number }>
    ) => {
      const conv = state.conversations.find(c => c.id === state.activeConversationId);
      if (!conv) return;
      const msg = conv.messages.find(m => m.id === action.payload.messageId);
      if (!msg || !msg.branches) return;
      msg.currentBranchIndex = action.payload.branchIndex;
    },
    replaceConversationTail: (
      state,
      action: PayloadAction<{
        conversationId: string;
        head: Message[];
        tail: Message[];
      }>
    ) => {
      const conv = state.conversations.find(c => c.id === action.payload.conversationId);
      if (!conv) return;
      conv.messages = [...action.payload.head, ...action.payload.tail];
      conv.updatedAt = new Date().toISOString();
    },
    deleteConversation: (state, action: PayloadAction<string>) => {
      state.conversations = state.conversations.filter(conv => conv.id !== action.payload);
      if (state.activeConversationId === action.payload) {
        state.activeConversationId = state.conversations[0]?.id || null;
      }
    },
    addMessage: (state, action: PayloadAction<{ conversationId: string; message: Message }>) => {
      const conversation = state.conversations.find(conv => conv.id === action.payload.conversationId);
      if (conversation) {
        conversation.messages.push(action.payload.message);
        conversation.updatedAt = new Date().toISOString();
        if (conversation.title === 'New Chat' && action.payload.message.sender === 'User') {
          conversation.title = action.payload.message.text.slice(0, 30) + (action.payload.message.text.length > 30 ? '...' : '');
        }
      }
    },
    // ✅ CRITICAL FIX: Enhanced message updating with proper text handling
    updateMessageText: (state, action: PayloadAction<{ 
  conversationId: string; 
  messageId: string; 
  newText: string 
}>) => {
  console.log('🔄 updateMessageText called:', {
    conversationId: action.payload.conversationId,
    messageId: action.payload.messageId,
    newTextLength: action.payload.newText?.length,
    newTextPreview: action.payload.newText?.substring(0, 200),
    containsImage: action.payload.newText?.includes('![')
  });
  
  const conversation = state.conversations.find(conv => conv.id === action.payload.conversationId);
  if (conversation) {
    const message = conversation.messages.find(msg => msg.id === action.payload.messageId);
    if (message) {
      console.log('✅ Message found, updating text');
      message.text = action.payload.newText;
      message.isStreaming = false;
      conversation.updatedAt = new Date().toISOString();
    } else {
      console.error('❌ Message not found:', action.payload.messageId);
    }
  } else {
    console.error('❌ Conversation not found:', action.payload.conversationId);
  }
},

    addBotMessage: (state, action: PayloadAction<string>) => {
      const conversation = state.conversations.find(conv => conv.id === state.activeConversationId);
      if (conversation) {
        const botMessage: Message = {
          id: generateId(),
          sender: 'Bot',
          text: action.payload,
          isStreaming: true,
          timestamp: new Date().toISOString(),
        };
        conversation.messages.push(botMessage);
        state.streamingMessageIndex = conversation.messages.length - 1;
        conversation.updatedAt = new Date().toISOString();
      }
    },
    appendToLastBotMessage: (state, action: PayloadAction<string>) => {
      const conversation = state.conversations.find(conv => conv.id === state.activeConversationId);
      if (conversation && state.streamingMessageIndex !== null) {
        conversation.messages[state.streamingMessageIndex].text += action.payload;
        conversation.updatedAt = new Date().toISOString();
      }
    },
    finishStreaming: (state) => {
      const conversation = state.conversations.find(conv => conv.id === state.activeConversationId);
      if (conversation && state.streamingMessageIndex !== null) {
        conversation.messages[state.streamingMessageIndex].isStreaming = false;
        state.streamingMessageIndex = null;
        conversation.updatedAt = new Date().toISOString();
      }
    },
    toggleMessageEdit: (state, action: PayloadAction<string>) => {
      const conversation = state.conversations.find(conv => conv.id === state.activeConversationId);
      if (conversation) {
        const message = conversation.messages.find(msg => msg.id === action.payload);
        if (message && message.sender === 'User') {
          message.isEditing = !message.isEditing;
        }
      }
    },
    updateMessageAndTruncate: (
      state,
      action: PayloadAction<{ messageId: string; newText: string; files?: FileData[] }>
    ) => {
      const conversation = state.conversations.find(
        (c) => c.id === state.activeConversationId
      );
      if (!conversation) return;

      const idx = conversation.messages.findIndex(
        (m) => m.id === action.payload.messageId
      );
      if (idx === -1) return;

      const msg = conversation.messages[idx];

      if (!msg.edits) {
        msg.edits = [msg.text];
      }

      msg.edits.push(action.payload.newText);
      msg.currentEditIndex = msg.edits.length - 1;
      msg.text = action.payload.newText;
      msg.files = action.payload.files || [];
      msg.isEditing = false;
      msg.timestamp = new Date().toISOString();

      conversation.messages = conversation.messages.slice(0, idx + 1);
      conversation.updatedAt = new Date().toISOString();
    },
    navigateUserEditVersion: (
      state,
      action: PayloadAction<{ messageId: string; direction: 'prev' | 'next' }>
    ) => {
      const conversation = state.conversations.find(
        (c) => c.id === state.activeConversationId
      );
      if (!conversation) return;

      const msg = conversation.messages.find(
        (m) => m.id === action.payload.messageId
      );
      if (!msg || !msg.edits || msg.edits.length < 2) return;

      const current = msg.currentEditIndex ?? (msg.edits.length - 1);
      const nextIndex =
        action.payload.direction === 'prev'
          ? Math.max(0, current - 1)
          : Math.min(msg.edits.length - 1, current + 1);

      msg.currentEditIndex = nextIndex;
      msg.text = msg.edits[nextIndex];
      conversation.updatedAt = new Date().toISOString();
    },
    navigateResponseVersion: (state, action: PayloadAction<{ messageId: string; direction: 'prev' | 'next' }>) => {
      const conversation = state.conversations.find(conv => conv.id === state.activeConversationId);
      if (conversation) {
        const message = conversation.messages.find(msg => msg.id === action.payload.messageId);
        if (message && message.responses && message.responses.length > 1) {
          const currentIndex = message.currentResponseIndex || 0;
          let newIndex: number;

          if (action.payload.direction === 'prev') {
            newIndex = Math.max(0, currentIndex - 1);
          } else {
            newIndex = Math.min(message.responses.length - 1, currentIndex + 1);
          }

          message.currentResponseIndex = newIndex;
          message.text = message.responses[newIndex];
          conversation.updatedAt = new Date().toISOString();
        }
      }
    },
    addResponseVersion: (state, action: PayloadAction<{ messageId: string; newResponse: string }>) => {
      const conversation = state.conversations.find(conv => conv.id === state.activeConversationId);
      if (conversation) {
        const message = conversation.messages.find(msg => msg.id === action.payload.messageId);
        if (message && message.sender === 'Bot') {
          if (!message.responses) {
            message.responses = [message.text];
          }

          message.responses.push(action.payload.newResponse);
          message.currentResponseIndex = message.responses.length - 1;
          message.text = action.payload.newResponse;
          conversation.updatedAt = new Date().toISOString();
        }
      }
    },
    // Enhanced image handling reducers
    clearGeneratedImage: (state) => {
      state.generatedImageUrl = null;
      state.imageError = null;
    },
    addToImageHistory: (state, action: PayloadAction<{ prompt: string; url: string }>) => {
      state.imageHistory.push({
        prompt: action.payload.prompt,
        url: action.payload.url,
        timestamp: new Date().toISOString()
      });
      state.currentImageIndex = state.imageHistory.length - 1;
    },
    // Clear all tool states
    clearToolStates: (state) => {
      state.searchResults = [];
      state.searchError = null;
      state.generatedImageUrl = null;
      state.imageError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch models reducers
      .addCase(fetchAvailableModels.pending, (state) => {
        state.modelsLoading = true;
        state.modelsError = null;
      })
      .addCase(fetchAvailableModels.fulfilled, (state, action) => {
        state.modelsLoading = false;
        state.availableModels = action.payload;
        state.modelsError = null;
        if (!action.payload.find(model => model.name === state.selectedModel)) {
          state.selectedModel = action.payload[0]?.name || 'mistral-large';
        }
      })
      .addCase(fetchAvailableModels.rejected, (state, action) => {
        state.modelsLoading = false;
        state.modelsError = action.error.message || 'Failed to fetch models';
      })

      // Chat message reducers
      .addCase(sendChatMessageStream.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(sendChatMessageStream.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(sendChatMessageStream.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Something went wrong';
        state.streamingMessageIndex = null;
      })

      // Regenerate-from-user thunk with enhanced branching
      .addCase(regenerateFromMessage.pending, (state, action) => {
        state.isLoading = true;
        state.error = null;

        const conv = state.conversations.find(c => c.id === state.activeConversationId);
        if (!conv) return;
        const idx = conv.messages.findIndex(m => m.id === action.meta.arg.messageId);
        if (idx < 0) return;

        const userMsg = conv.messages[idx];
        const oldTail = conv.messages.slice(idx + 1);

        if (!userMsg.branches) {
          userMsg.branches = [];
          userMsg.currentBranchIndex = 0;
        }
        if (userMsg.branches.length === 0) {
          userMsg.branches.push(oldTail);
        }

        conv.messages = conv.messages.slice(0, idx + 1);
      })
      .addCase(regenerateFromMessage.fulfilled, (state, action) => {
        state.isLoading = false;
        state.error = null;

        const conv = state.conversations.find(c => c.id === state.activeConversationId);
        if (!conv) return;
        const idx = conv.messages.findIndex(m => m.id === action.meta.arg.messageId);
        if (idx < 0) return;

        const userMsg = conv.messages[idx];
        const newTail = conv.messages.slice(idx + 1);

        userMsg.branches!.push(newTail);
        userMsg.currentBranchIndex = userMsg.branches!.length - 1;
      })
      .addCase(regenerateFromMessage.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Regeneration failed';
        state.streamingMessageIndex = null;
      })

      // Regenerate-response thunk
      .addCase(regenerateResponse.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(regenerateResponse.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(regenerateResponse.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Response regeneration failed';
        state.streamingMessageIndex = null;
      })

      // Enhanced web search reducers
      .addCase(webSearch.pending, (state) => {
        state.searchLoading = true;
        state.searchError = null;
        state.searchResults = [];
      })
      .addCase(webSearch.fulfilled, (state, { payload }) => {
        state.searchLoading = false;
        state.searchResults = payload;
        state.searchError = null;
      })
      .addCase(webSearch.rejected, (state, { payload, error }) => {
        state.searchLoading = false;
        state.searchError = payload ?? error.message ?? 'Search failed';
        state.searchResults = [];
      })

      // ✅ ENHANCED image generation reducers with proper state management
      .addCase(generateImage.pending, (state, action) => {
        console.log('🔄 Image generation pending for prompt:', action.meta.arg.prompt);
        state.imageLoading = true;
        state.imageError = null;
        // DON'T clear generatedImageUrl here - let it stay until new image is ready
      })
      .addCase(generateImage.fulfilled, (state, { payload, meta }) => {
        console.log('✅ Image generation fulfilled with URL:', payload?.substring(0, 50));
        state.imageLoading = false;
        state.generatedImageUrl = payload;
        state.imageError = null;
        
        // Add to image history
        state.imageHistory.push({
          prompt: meta.arg.prompt,
          url: payload,
          timestamp: new Date().toISOString()
        });
        state.currentImageIndex = state.imageHistory.length - 1;
      })
      .addCase(generateImage.rejected, (state, { payload, error, meta }) => {
        console.error('❌ Image generation rejected:', payload || error.message);
        state.imageLoading = false;
        state.imageError = payload ?? error.message ?? 'Image generation failed';
        // Don't clear generatedImageUrl on error - keep previous image if any
      });
  },
});

export const {
  setInput,
  setSelectedModel,
  setActiveTool,
  createNewConversation,
  switchConversation,
  deleteConversation,
  addMessage,
  updateMessageText, // ✅ CRITICAL: This is the missing action that fixes image rendering
  addBotMessage,
  appendToLastBotMessage,
  finishStreaming,
  toggleMessageEdit,
  updateMessageAndTruncate,
  navigateResponseVersion,
  addResponseVersion,
  navigateUserEditVersion,
  replaceConversationTail,
  setUserBranchIndex,
  clearGeneratedImage,
  addToImageHistory,
  clearToolStates,
} = chatSlice.actions;

export default chatSlice.reducer;
