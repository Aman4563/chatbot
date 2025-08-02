// page.tsx

"use client";

import React, { useEffect } from 'react';
import './globals.css';
import { Provider } from "react-redux";
import { store } from "../store";
import { useDispatch } from 'react-redux';
import Sidebar from '@/Component/Sidebar';
import Chat from '@/Component/Chat';
import { fetchAvailableModels } from '../chatSlice';

// Create a wrapper component to handle model fetching
const AppContent = () => {
  const dispatch = useDispatch();

  useEffect(() => {
    // Fetch available models when the app loads
    dispatch(fetchAvailableModels());
  }, [dispatch]);

  return (
    <div className="h-screen flex bg-slate-100">
      <Sidebar />
      <Chat />
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
