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
import { fetchAvailableModels } from '../chatSlice';

// Create a wrapper component to handle model fetching
const AppContent = () => {
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    // Fetch available models when the app loads
    dispatch(fetchAvailableModels());
  }, [dispatch]);

  return (
    <div className="h-screen flex flex-col md:flex-row bg-slate-100">
      <Sidebar />
      <main className="flex-1 min-w-0 relative">
        <Chat />
      </main>
    </div>
  );
};

export default function Home() {
  return (
    <Provider store={store}>
      <AppContent />
    </Provider>
  );
}
