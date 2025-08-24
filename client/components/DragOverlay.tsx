import React from 'react';
import { Upload } from 'lucide-react';

export const DragOverlay: React.FC = () => {
  return (
    <div className="absolute inset-0 bg-blue-100/90 backdrop-blur-sm flex items-center justify-center z-50 border-2 border-dashed border-blue-400 m-4 rounded-2xl">
      <div className="text-center">
        <div className="w-16 h-16 bg-blue-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <Upload className="w-8 h-8 text-white" />
        </div>
        <p className="text-xl font-bold text-blue-800 mb-1">Drop files here to upload</p>
        <p className="text-blue-600">Images, documents, and more</p>
      </div>
    </div>
  );
};
