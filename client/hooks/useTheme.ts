import { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { applyThemeToDOM, isDarkMode } from '../utils/themeUtils';

export type Theme = 'light' | 'dark' | 'auto';

export const useTheme = () => {
  const { websiteTheme } = useSelector((state: RootState) => state.settings);
  const [currentTheme, setCurrentTheme] = useState<Theme>('auto');
  const [isDark, setIsDark] = useState(false);
  const [isClient, setIsClient] = useState(false);

  // Check if we're on the client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Get the actual applied theme (resolves 'auto' to light/dark)
  const getAppliedTheme = (theme: Theme): 'light' | 'dark' => {
    if (theme === 'auto') {
      // Only access window on client side
      if (typeof window !== 'undefined' && window.matchMedia) {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      // Default to light theme during SSR
      return 'light';
    }
    return theme;
  };

  // Apply theme to DOM
  const applyTheme = (theme: Theme) => {
    // Only apply theme on client side
    if (typeof window !== 'undefined') {
      applyThemeToDOM(theme);
      setIsDark(isDarkMode());
    }
  };

  // Initialize theme from localStorage
  useEffect(() => {
    if (!isClient) return; // Skip during SSR

    try {
      const saved = localStorage.getItem('chatbot-settings');
      if (saved) {
        const parsed = JSON.parse(saved);
        const savedTheme = parsed.websiteTheme || 'auto';
        setCurrentTheme(savedTheme);
        applyTheme(savedTheme);
      }
    } catch (error) {
      console.warn('Failed to load theme from localStorage:', error);
    }
  }, [isClient]);

  // Apply theme when Redux state changes
  useEffect(() => {
    if (!isClient) return; // Skip during SSR

    setCurrentTheme(websiteTheme);
    applyTheme(websiteTheme);
  }, [websiteTheme, isClient]);

  // Listen for system theme changes when auto is selected
  useEffect(() => {
    if (!isClient || currentTheme !== 'auto') return; // Skip during SSR or if not auto

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      applyTheme('auto');
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [currentTheme, isClient]);

  return {
    theme: currentTheme,
    isDark,
    appliedTheme: getAppliedTheme(currentTheme),
    applyTheme,
    isClient
  };
};
