"use client";

import React, { createContext, useContext, ReactNode } from 'react';
import { useTheme } from '../hooks/useTheme';

interface ThemeContextType {
  theme: 'light' | 'dark' | 'auto';
  isDark: boolean;
  appliedTheme: 'light' | 'dark';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useThemeContext = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useThemeContext must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeContextProviderProps {
  children: ReactNode;
}

export const ThemeContextProvider: React.FC<ThemeContextProviderProps> = ({ children }) => {
  const { theme, isDark, appliedTheme } = useTheme();

  return (
    <ThemeContext.Provider value={{ theme, isDark, appliedTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
