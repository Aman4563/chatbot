"use client";

import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { useTheme } from '../hooks/useTheme';

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const { fontSize, compactMode } = useSelector((state: RootState) => state.settings);
  const { theme, isDark, appliedTheme } = useTheme();

  // Update debug indicator
  const updateDebugIndicator = (theme: string) => {
    const debugElement = document.getElementById('theme-debug');
    if (debugElement) {
      debugElement.textContent = `${theme} (${appliedTheme})`;
    }
  };

  // Update debug indicator when theme changes
  useEffect(() => {
    updateDebugIndicator(theme);
  }, [theme, appliedTheme]);

  // Apply font size and compact mode
  useEffect(() => {
    const root = document.documentElement;
    
    // Apply font size
    root.style.fontSize = fontSize === 'small' ? '14px' : fontSize === 'large' ? '18px' : '16px';

    // Apply compact mode
    if (compactMode) {
      root.classList.add('compact-mode');
    } else {
      root.classList.remove('compact-mode');
    }
  }, [fontSize, compactMode]);

  return <>{children}</>;
};
