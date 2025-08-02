// chatSlice.ts

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
  
 // —— add these two —— 
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

// NEW: Model info interface matching backend
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
  availableModels: ModelInfo[]; // Changed from string[] to ModelInfo[]
  modelsLoading: boolean;
  modelsError: string | null;
    searchResults: string[];
  searchLoading: boolean;
  searchError: string | null;
  generatedImageUrl: string | null;
  imageLoading: boolean;
  imageError: string | null;
}



const initialState: ChatState = {
  conversations: [],
  activeConversationId: null,
  input: '',
  isLoading: false,
  error: null,
  streamingMessageIndex: null,
  selectedModel: 'mistral-large', // Changed default to Mistral
  availableModels: [],
  modelsLoading: false,
  modelsError: null,
    searchResults: [],
  searchLoading: false,
  searchError: null,
  generatedImageUrl: null,
  imageLoading: false,
  imageError: null,
};

const generateId = () => Date.now().toString() + Math.random().toString(36).substr(2, 9);

// Convert messages to history format for API
const formatHistoryForAPI = (messages: Message[]) => {
  return messages.map(msg => ({
    role: msg.sender === 'User' ? 'user' : 'assistant',
    content: msg.text,
    files: msg.files || []
  }));
};


// 2️⃣ Define your new tool-calling thunks
export const webSearch = createAsyncThunk<
  string[],                             // returned payload: array of URLs
  { query: string; num_results?: number }, // thunk arg
  { rejectValue: string }
>(
  'chat/webSearch',
  async ({ query, num_results = 5 }, { rejectWithValue }) => {
    try {
      const res = await fetch(
  `${API_BASE}/tools/search?q=${encodeURIComponent(query)}&num_results=${num_results}`
);
      if (!res.ok) {
        const text = await res.text();
        return rejectWithValue(text || 'Search failed');
      }
      const json = (await res.json()) as { query: string; results: string[] };
      return json.results;
    } catch (err: any) {
      return rejectWithValue(err.message ?? 'Network error');
    }
  }
);

export const generateImage = createAsyncThunk<
  string,                   // returned payload: image URL
  { prompt: string },       // thunk arg
  { rejectValue: string }
>(
  'chat/generateImage',
  async ({ prompt }, { rejectWithValue }) => {
    try {
      const res = await fetch(
  `${API_BASE}/tools/image`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  }
);

      if (!res.ok) {
        const text = await res.text();
        return rejectWithValue(text || 'Image generation failed');
      }
      const json = (await res.json()) as { prompt: string; url: string };
      return json.url;
    } catch (err: any) {
      return rejectWithValue(err.message ?? 'Network error');
    }
  }
);


// NEW: Fetch available models from backend
export const fetchAvailableModels = createAsyncThunk(
  'chat/fetchAvailableModels',
  async () => {
    const response = await fetch('http://localhost:8000/models');
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

    // Get current conversation for context
    const currentConversation = conversations.find(conv => conv.id === activeConversationId);
    const history = currentConversation ? formatHistoryForAPI(currentConversation.messages) : [];

    console.log('Sending with history:', history);
    console.log('Using model:', selectedModel);

    const response = await fetch('http://localhost:8000/chat', {
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

    // Get history up to (but not including) the edited message
    const historyMessages = currentConversation.messages.slice(0, messageIndex);
    const history = formatHistoryForAPI(historyMessages);

    // Update the message and remove all subsequent messages
    dispatch(updateMessageAndTruncate({ messageId, newText, files }));

    const response = await fetch('http://localhost:8000/chat', {
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

    // Get the user message that prompted this bot response
    const userMessage = messageIndex > 0 ? currentConversation.messages[messageIndex - 1] : null;
    if (!userMessage || userMessage.sender !== 'User') {
      throw new Error('No user message found to regenerate from');
    }

    // Get history up to the user message
    const historyMessages = currentConversation.messages.slice(0, messageIndex - 1);
    const history = formatHistoryForAPI(historyMessages);

    const response = await fetch('http://localhost:8000/chat', {
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

    // Handle streaming response and add to responses array
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
      // Update active conversation model
      if (state.activeConversationId) {
        const conversation = state.conversations.find(conv => conv.id === state.activeConversationId);
        if (conversation) {
          conversation.model = action.payload;
        }
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
    },
    switchConversation: (state, action: PayloadAction<string>) => {
      state.activeConversationId = action.payload;
      state.streamingMessageIndex = null;
      // Update selected model based on conversation
      const conversation = state.conversations.find(conv => conv.id === action.payload);
      if (conversation) {
        state.selectedModel = conversation.model;
      }
    },
      // inside your createSlice({ reducers: { … }})

// switch which branch of continuation to show 
setUserBranchIndex( 
   state, 
   action: PayloadAction<{ messageId: string; branchIndex: number }>
 ) {
   const conv = state.conversations.find(c => c.id === state.activeConversationId);
   if (!conv) return; 
   const msg = conv.messages.find(m => m.id === action.payload.messageId);
   if (!msg || !msg.branches) return;
   msg.currentBranchIndex = action.payload.branchIndex; 
 },

 // rebuild the conversation tail from head + that branch
 replaceConversationTail(
   state,
   action: PayloadAction<{
     conversationId: string;
     head: Message[]; 
     tail: Message[];
   }>
 ) {
   const conv = state.conversations.find(c => c.id === action.payload.conversationId);
   if (!conv) return;
   conv.messages = [...action.payload.head, ...action.payload.tail];
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

    // ——— Regenerate-from-user thunk ———
    .addCase(regenerateFromMessage.pending, (state, action) => {
      state.isLoading = true;
      state.error = null;

      // 1) Find the conversation & user message
      const conv = state.conversations.find(c => c.id === state.activeConversationId);
      if (!conv) return;
      const idx = conv.messages.findIndex(m => m.id === action.meta.arg.messageId);
      if (idx < 0) return;

      const userMsg = conv.messages[idx];

      // 2) Capture the old tail (everything after this user message)
      const oldTail = conv.messages.slice(idx + 1);

      // 3) Initialize branches on first regen
      if (!userMsg.branches) {
        userMsg.branches = [];
        userMsg.currentBranchIndex = 0;
      }
      // 4) Stash the original tail as branch #0 (only once)
      if (userMsg.branches.length === 0) {
        userMsg.branches.push(oldTail);
      }

      // 5) Truncate the conversation to just up through this user message
      conv.messages = conv.messages.slice(0, idx + 1);
    })
    .addCase(regenerateFromMessage.fulfilled, (state, action) => {
      state.isLoading = false;
      state.error = null;

      // 1) Locate the same user message
      const conv = state.conversations.find(c => c.id === state.activeConversationId);
      if (!conv) return;
      const idx = conv.messages.findIndex(m => m.id === action.meta.arg.messageId);
      if (idx < 0) return;

      const userMsg = conv.messages[idx];

      // 2) Capture the new tail (the freshly streamed bot messages)
      const newTail = conv.messages.slice(idx + 1);

      // 3) Add it as branch #1 (or next index) and switch to it
      userMsg.branches!.push(newTail);
      userMsg.currentBranchIndex = userMsg.branches!.length - 1;
    })
    .addCase(regenerateFromMessage.rejected, (state, action) => {
      state.isLoading = false;
      state.error = action.error.message || 'Regeneration failed';
      state.streamingMessageIndex = null;
    })

    // Regenerate-response thunk (single‐message regen)  
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
    .addCase(webSearch.pending, (state) => {
      state.searchLoading = true;
      state.searchError = null;
    })
    .addCase(webSearch.fulfilled, (state, { payload }) => {
      state.searchLoading = false;
      state.searchResults = payload;
    })
    .addCase(webSearch.rejected, (state, { payload, error }) => {
      state.searchLoading = false;
      state.searchError = payload ?? error.message ?? 'Search failed';
    })

    // Image-generation tool cases
    .addCase(generateImage.pending, (state) => {
      state.imageLoading = true;
      state.imageError = null;
    })
    .addCase(generateImage.fulfilled, (state, { payload }) => {
      state.imageLoading = false;
      state.generatedImageUrl = payload;
    })
    .addCase(generateImage.rejected, (state, { payload, error }) => {
      state.imageLoading = false;
      state.imageError = payload ?? error.message ?? 'Image generation failed';
    });
},

});

export const {
  setInput,
  setSelectedModel,
  createNewConversation,
  switchConversation,
  deleteConversation,
  addMessage,
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
} = chatSlice.actions;

export default chatSlice.reducer;
