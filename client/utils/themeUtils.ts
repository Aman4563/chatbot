import { Theme } from '../hooks/useTheme';

// Theme class utilities
export const getThemeClasses = (baseClasses: string, darkClasses: string = '') => {
  return `${baseClasses} ${darkClasses}`.trim();
};

// Common theme-aware class combinations
export const themeClasses = {
  // Backgrounds
  bg: {
    primary: 'bg-white dark:bg-gray-900',
    secondary: 'bg-gray-50 dark:bg-gray-800',
    tertiary: 'bg-gray-100 dark:bg-gray-700',
    sidebar: 'bg-slate-100 dark:bg-slate-900',
    modal: 'bg-white dark:bg-gray-800',
    card: 'bg-white dark:bg-gray-800',
  },
  
  // Text colors
  text: {
    primary: 'text-gray-900 dark:text-gray-100',
    secondary: 'text-gray-700 dark:text-gray-300',
    tertiary: 'text-gray-500 dark:text-gray-400',
    muted: 'text-gray-400 dark:text-gray-500',
    inverse: 'text-white dark:text-gray-900',
  },
  
  // Borders
  border: {
    primary: 'border-gray-200 dark:border-gray-700',
    secondary: 'border-gray-300 dark:border-gray-600',
    accent: 'border-blue-200 dark:border-blue-700',
  },
  
  // Interactive states
  hover: {
    bg: 'hover:bg-gray-50 dark:hover:bg-gray-700',
    text: 'hover:text-gray-900 dark:hover:text-gray-100',
  },
  
  // Focus states
  focus: {
    ring: 'focus:ring-blue-500 dark:focus:ring-blue-400',
    border: 'focus:border-blue-500 dark:focus:border-blue-400',
  },
};

// Apply theme to HTML element
export const applyThemeToDOM = (theme: Theme) => {
  const root = document.documentElement;
  
  // Remove any existing theme classes
  root.classList.remove('light', 'dark');
  
  // Apply the appropriate theme
  if (theme === 'dark') {
    root.classList.add('dark');
  } else if (theme === 'light') {
    root.classList.add('light');
  } else if (theme === 'auto') {
    // Auto mode - use system preference
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      root.classList.add('dark');
    } else {
      root.classList.add('light');
    }
  }
  
  // Set data attribute for CSS targeting
  const appliedTheme = theme === 'auto' 
    ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : theme;
  root.setAttribute('data-theme', appliedTheme);
};

// Check if dark mode is active
export const isDarkMode = (): boolean => {
  if (typeof window === 'undefined') return false;
  
  // Check for dark class
  if (document.documentElement.classList.contains('dark')) {
    return true;
  }
  
  // Check for light class
  if (document.documentElement.classList.contains('light')) {
    return false;
  }
  
  // Fallback to system preference
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
};

// Get current theme from DOM
export const getCurrentTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light';
  
  const root = document.documentElement;
  
  if (root.classList.contains('dark')) {
    return 'dark';
  }
  
  if (root.classList.contains('light')) {
    return 'light';
  }
  
  // Fallback to system preference
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};
