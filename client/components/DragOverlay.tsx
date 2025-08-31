import React from 'react';
import { Upload, FileText, Image as ImageIcon, File } from 'lucide-react';

export const DragOverlay: React.FC = () => {
  return (
    <div 
      className="absolute inset-0 flex items-center justify-center z-50 m-4 rounded-3xl overflow-hidden"
      role="dialog"
      aria-label="File drop zone"
      aria-describedby="drop-zone-description"
    >
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 via-purple-500/15 to-indigo-500/20 backdrop-blur-xl animate-pulse" />
      <div className="absolute inset-0 border-2 border-dashed border-blue-400/60 rounded-3xl animate-pulse" />
      
      {/* Floating Icons Animation */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <FileText className="absolute top-1/4 left-1/4 w-6 h-6 text-blue-400/40 animate-bounce" style={{ animationDelay: '0s' }} />
        <ImageIcon className="absolute top-1/3 right-1/4 w-5 h-5 text-purple-400/40 animate-bounce" style={{ animationDelay: '0.5s' }} />
        <File className="absolute bottom-1/3 left-1/3 w-4 h-4 text-indigo-400/40 animate-bounce" style={{ animationDelay: '1s' }} />
      </div>

      {/* Main Content */}
      <div className="relative text-center px-8 py-6 max-w-md">
        {/* Icon Container with Gradient */}
        <div className="relative mx-auto mb-6">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl flex items-center justify-center shadow-xl shadow-blue-500/25 transform hover:scale-105 transition-transform duration-300">
            <Upload className="w-10 h-10 text-white animate-pulse" />
          </div>
          {/* Glow Effect */}
          <div className="absolute inset-0 w-20 h-20 bg-gradient-to-br from-blue-400 to-purple-500 rounded-3xl blur-xl opacity-30 animate-pulse" />
        </div>

        {/* Text Content */}
        <div className="space-y-2">
          <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Drop files here
          </h3>
          <p 
            id="drop-zone-description"
            className="text-blue-600/80 font-medium"
          >
            Upload images, documents, PDFs, and more
          </p>
          <div className="flex items-center justify-center gap-2 mt-4 text-sm text-blue-500/70">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" aria-hidden="true" />
            <span>Ready to process your files</span>
          </div>
        </div>

        {/* Supported Formats */}
        <div className="mt-6 flex items-center justify-center gap-3 text-xs text-blue-500/60">
          <span className="px-2 py-1 bg-blue-100/50 rounded-lg">Images</span>
          <span className="px-2 py-1 bg-purple-100/50 rounded-lg">PDFs</span>
          <span className="px-2 py-1 bg-indigo-100/50 rounded-lg">Documents</span>
        </div>
      </div>
    </div>
  );
};
