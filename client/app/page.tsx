// page.tsx
"use client";

import React from 'react';
import './globals.css';
import { Provider } from "react-redux";
import { store } from "../store";
import Sidebar from '@/Component/Sidebar';
import Chat from '@/Component/Chat';

export default function Home() {
  return (
    <Provider store={store}>
      <div style={{ display: 'flex', height: '100vh' }}>
        <Sidebar />
        <div style={{ flex: 1 }}>
          <Chat />
        </div>
      </div>
    </Provider>
  );
}
