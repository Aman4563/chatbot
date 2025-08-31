import React from 'react';
import { AlertCircle } from 'lucide-react';

interface ErrorDisplayProps {
  error: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error }) => {
  return (
    <div className="bg-red-50/95 dark:bg-red-900/20 backdrop-blur-sm border-t border-red-200 dark:border-red-800">
      <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-3 text-red-800 dark:text-red-200">
        <div className="w-8 h-8 bg-red-100 dark:bg-red-900/40 rounded-lg flex items-center justify-center flex-shrink-0">
          <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
        </div>
        <span className="text-sm font-medium">
          <strong>Error:</strong> {error}
        </span>
      </div>
    </div>
  );
};
