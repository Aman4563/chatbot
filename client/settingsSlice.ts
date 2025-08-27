import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface SettingsState {
  // Theme settings
  websiteTheme: 'light' | 'dark' | 'auto';
  codeBlockTheme: string;
  
  // Code block settings
  showLineNumbers: boolean;
  showLanguageBadge: boolean;
  autoWrapCode: boolean;
  
  // UI settings
  fontSize: 'small' | 'medium' | 'large';
  compactMode: boolean;
  
  // Chat settings
  autoScroll: boolean;
  showTypingIndicator: boolean;
}

// Load settings from localStorage synchronously
const loadSettings = (): SettingsState => {
  // Default settings
  const defaultSettings: SettingsState = {
    websiteTheme: 'auto',
    codeBlockTheme: 'dracula',
    showLineNumbers: true,
    showLanguageBadge: true,
    autoWrapCode: false,
    fontSize: 'medium',
    compactMode: false,
    autoScroll: true,
    showTypingIndicator: true,
  };

  // Only try to load from localStorage if we're in a browser environment
  if (typeof window === 'undefined') {
    return defaultSettings;
  }

  try {
    const saved = localStorage.getItem('chatbot-settings');
    if (saved) {
      const parsed = JSON.parse(saved);
      return {
        websiteTheme: parsed.websiteTheme || 'auto',
        codeBlockTheme: parsed.codeBlockTheme || 'dracula',
        showLineNumbers: parsed.showLineNumbers !== undefined ? parsed.showLineNumbers : true,
        showLanguageBadge: parsed.showLanguageBadge !== undefined ? parsed.showLanguageBadge : true,
        autoWrapCode: parsed.autoWrapCode !== undefined ? parsed.autoWrapCode : false,
        fontSize: parsed.fontSize || 'medium',
        compactMode: parsed.compactMode !== undefined ? parsed.compactMode : false,
        autoScroll: parsed.autoScroll !== undefined ? parsed.autoScroll : true,
        showTypingIndicator: parsed.showTypingIndicator !== undefined ? parsed.showTypingIndicator : true,
      };
    }
  } catch (error) {
    console.warn('Failed to load settings from localStorage:', error);
  }

  return defaultSettings;
};

const initialState: SettingsState = loadSettings();

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setWebsiteTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.websiteTheme = action.payload;
      // Save to localStorage
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('chatbot-settings', JSON.stringify(state));
        } catch (error) {
          console.warn('Failed to save settings to localStorage:', error);
        }
      }
    },
    setCodeBlockTheme: (state, action: PayloadAction<string>) => {
      state.codeBlockTheme = action.payload;
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('chatbot-settings', JSON.stringify(state));
        } catch (error) {
          console.warn('Failed to save settings to localStorage:', error);
        }
      }
    },
    setShowLineNumbers: (state, action: PayloadAction<boolean>) => {
      state.showLineNumbers = action.payload;
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('chatbot-settings', JSON.stringify(state));
        } catch (error) {
          console.warn('Failed to save settings to localStorage:', error);
        }
      }
    },
    setShowLanguageBadge: (state, action: PayloadAction<boolean>) => {
      state.showLanguageBadge = action.payload;
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('chatbot-settings', JSON.stringify(state));
        } catch (error) {
          console.warn('Failed to save settings to localStorage:', error);
        }
      }
    },
    setAutoWrapCode: (state, action: PayloadAction<boolean>) => {
      state.autoWrapCode = action.payload;
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('chatbot-settings', JSON.stringify(state));
        } catch (error) {
          console.warn('Failed to save settings to localStorage:', error);
        }
      }
    },
    setFontSize: (state, action: PayloadAction<'small' | 'medium' | 'large'>) => {
      state.fontSize = action.payload;
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('chatbot-settings', JSON.stringify(state));
        } catch (error) {
          console.warn('Failed to save settings to localStorage:', error);
        }
      }
    },
    setCompactMode: (state, action: PayloadAction<boolean>) => {
      state.compactMode = action.payload;
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('chatbot-settings', JSON.stringify(state));
        } catch (error) {
          console.warn('Failed to save settings to localStorage:', error);
        }
      }
    },
    setAutoScroll: (state, action: PayloadAction<boolean>) => {
      state.autoScroll = action.payload;
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('chatbot-settings', JSON.stringify(state));
        } catch (error) {
          console.warn('Failed to save settings to localStorage:', error);
        }
      }
    },
    setShowTypingIndicator: (state, action: PayloadAction<boolean>) => {
      state.showTypingIndicator = action.payload;
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('chatbot-settings', JSON.stringify(state));
        } catch (error) {
          console.warn('Failed to save settings to localStorage:', error);
        }
      }
    },
  },
});

export const {
  setWebsiteTheme,
  setCodeBlockTheme,
  setShowLineNumbers,
  setShowLanguageBadge,
  setAutoWrapCode,
  setFontSize,
  setCompactMode,
  setAutoScroll,
  setShowTypingIndicator,
} = settingsSlice.actions;

export default settingsSlice.reducer;