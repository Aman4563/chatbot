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
  sender: string;
  text: string;
  files?: FileData[];
  isStreaming?: boolean;
  timestamp: string;
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
        history: history, // NOW PROPERLY SENDING HISTORY
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
  finishStreaming 
} = chatSlice.actions;

export default chatSlice.reducer;
