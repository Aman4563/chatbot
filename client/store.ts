// store.ts
import { configureStore } from '@reduxjs/toolkit';
import chatReducer from './chatSlice';

export const store = configureStore({
  reducer: {
    chat: chatReducer,
  },
});

// Types for use in typed hooks and components
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
