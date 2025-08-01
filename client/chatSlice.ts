// chatSlice.ts
import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';

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
  isEditing?: boolean;              // toggle edit‐mode
  responses?: string[];             // Bot response versions
  currentResponseIndex?: number;    // which Bot response is showing
  // ──────────────────────────────────────────────────────────────────────────
  edits?: string[];                 // NEW: User edit versions
  currentEditIndex?: number;        // NEW: which User edit is showing
};
export type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  model: string;
  createdAt: string;
  updatedAt: string;
};

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  input: string;
  isLoading: boolean;
  error: string | null;
  streamingMessageIndex: number | null;
  selectedModel: string;
  availableModels: string[];
}

const initialState: ChatState = {
  conversations: [],
  activeConversationId: null,
  input: '',
  isLoading: false,
  error: null,
  streamingMessageIndex: null,
  selectedModel: 'gemini-2.5-flash',
  availableModels: ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-2.5-pro'],
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

// NEW: Async thunk for regenerating response from a specific message
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

    // Find the message index
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

// NEW: Async thunk for regenerating new response versions
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
                // Add new response to the message
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
    // NEW: Toggle edit mode for a message
    toggleMessageEdit: (state, action: PayloadAction<string>) => {
      const conversation = state.conversations.find(conv => conv.id === state.activeConversationId);
      if (conversation) {
        const message = conversation.messages.find(msg => msg.id === action.payload);
        if (message && message.sender === 'User') {
          message.isEditing = !message.isEditing;
        }
      }
    },
    // NEW: Update message text and remove all subsequent messages
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

      // ─── Maintain an edit‐history array on the user message ───
      if (!msg.edits) {
        // first time editing → seed with original text
        msg.edits = [msg.text];
      }
      // push the newly saved text
      msg.edits.push(action.payload.newText);
      msg.currentEditIndex = msg.edits.length - 1;

      // ─── Now overwrite the message with the new text ───
      msg.text = action.payload.newText;
      msg.files = action.payload.files || [];
      msg.isEditing = false;
      msg.timestamp = new Date().toISOString();

      // ─── truncate any messages that came *after* this one ───
      conversation.messages = conversation.messages.slice(0, idx + 1);
      conversation.updatedAt = new Date().toISOString();
    },
        // NAVIGATE THROUGH USER EDIT VERSIONS
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

    // NEW: Navigate between response versions
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
    // NEW: Add new response version to a message
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
    }
  },
  extraReducers: (builder) => {
    builder
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
      // NEW: Handle regeneration states
      .addCase(regenerateFromMessage.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(regenerateFromMessage.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(regenerateFromMessage.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Regeneration failed';
        state.streamingMessageIndex = null;
      })
      // NEW: Handle regenerateResponse states
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
  toggleMessageEdit, // NEW
  updateMessageAndTruncate, // NEW
  navigateResponseVersion, // NEW
  addResponseVersion, // NEW
  navigateUserEditVersion,      // NEW

} = chatSlice.actions;

export default chatSlice.reducer;
