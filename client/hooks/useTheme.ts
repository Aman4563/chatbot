import { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { applyThemeToDOM, isDarkMode } from '../utils/themeUtils';

export type Theme = 'light' | 'dark' | 'auto';

export const useTheme = () => {
  const { websiteTheme } = useSelector((state: RootState) => state.settings);
  const [currentTheme, setCurrentTheme] = useState<Theme>('auto');
  const [isDark, setIsDark] = useState(false);

  // Get the actual applied theme (resolves 'auto' to light/dark)
  const getAppliedTheme = (theme: Theme): 'light' | 'dark' => {
    if (theme === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return theme;
  };

  // Apply theme to DOM
  const applyTheme = (theme: Theme) => {
    applyThemeToDOM(theme);
    setIsDark(isDarkMode());
    
    console.log(`Theme applied: ${theme} -> ${getAppliedTheme(theme)}`);
  };

  // Initialize theme from localStorage
  useEffect(() => {
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
  }, []);

  // Apply theme when Redux state changes
  useEffect(() => {
    setCurrentTheme(websiteTheme);
    applyTheme(websiteTheme);
  }, [websiteTheme]);

  // Listen for system theme changes when auto is selected
  useEffect(() => {
    if (currentTheme === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = () => {
        applyTheme('auto');
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [currentTheme]);

  return {
    theme: currentTheme,
    isDark,
    appliedTheme: getAppliedTheme(currentTheme),
    applyTheme
  };
};
