import React from 'react';
import { MessageCircle } from 'lucide-react';

export const EmptyState: React.FC = () => {
  return (
    <div className="flex-1 flex items-center justify-center empty-state">
      <div className="text-center max-w-md mx-auto px-6">
        <div className="w-20 h-20 empty-state-icon rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
          <MessageCircle className="w-10 h-10 text-white" />
        </div>
        <h3 className="text-2xl font-bold empty-state-title mb-3">Welcome to Xbot</h3>
        <p className="empty-state-text leading-relaxed">
          Create a new conversation to get started with our intelligent assistant
        </p>
      </div>
    </div>
  );
};
