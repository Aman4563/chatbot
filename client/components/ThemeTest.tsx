import React from 'react';
import { useThemeContext } from '../contexts/ThemeContext';

export const ThemeTest: React.FC = () => {
  const { theme, isDark, appliedTheme } = useThemeContext();

  return (
    <div className="fixed bottom-4 left-4 z-50 bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
      <div className="text-sm space-y-1">
        <div className="font-semibold text-gray-900 dark:text-gray-100">Theme Debug</div>
        <div className="text-gray-600 dark:text-gray-400">
          <div>Selected: {theme}</div>
          <div>Applied: {appliedTheme}</div>
          <div>Is Dark: {isDark ? 'Yes' : 'No'}</div>
        </div>
        <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-700 rounded text-xs">
          <div>HTML Classes: {document.documentElement.className}</div>
          <div>Data Theme: {document.documentElement.getAttribute('data-theme')}</div>
        </div>
      </div>
    </div>
  );
};
