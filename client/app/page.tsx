// page.tsx

"use client";

import React, { useEffect } from 'react';
import './globals.css';
import { Provider } from "react-redux";
import { store } from "../store";
import { useDispatch } from 'react-redux';
import type { AppDispatch } from '../store';
import Sidebar from '../Component/Sidebar';
import Chat from '../Component/Chat';
import { ThemeProvider } from '../components/ThemeProvider';
import { ThemeContextProvider } from '../contexts/ThemeContext';
import { ThemeTest } from '../components/ThemeTest';
import { fetchAvailableModels } from '../chatSlice';

// Create a wrapper component to handle model fetching
const AppContent = () => {
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    // Fetch available models when the app loads
    dispatch(fetchAvailableModels());
  }, [dispatch]);

  return (
    <ThemeContextProvider>
      <ThemeProvider>
        <div className="h-screen flex flex-col md:flex-row bg-slate-100 dark:bg-slate-900 transition-colors duration-300">
          {/* Debug indicator */}
          <div className="fixed top-2 right-2 z-50 bg-white dark:bg-gray-800 px-2 py-1 rounded text-xs border border-gray-200 dark:border-gray-700">
            Theme: <span id="theme-debug">Loading...</span>
          </div>
          
          {/* Theme test component */}
          <ThemeTest />
          
          <Sidebar />
          <main className="flex-1 min-w-0 relative">
            <Chat />
          </main>
        </div>
      </ThemeProvider>
    </ThemeContextProvider>
  );
};

export default function Home() {
  return (
    <Provider store={store}>
      <AppContent />
    </Provider>
  );
}
