import React from 'react';
import { Paperclip, X, Image as ImageIcon, FileCheck } from 'lucide-react';
import { FileData } from '../chatSlice';
import { FileIcon } from './shared/FileIcon';
import { getFileTypeColor } from '../utils/fileUtils';

interface FilePreviewProps {
  files: FileData[];
  onRemoveFile: (index: number) => void;
}

export const FilePreview: React.FC<FilePreviewProps> = ({ files, onRemoveFile }) => {

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const renderFilePreview = (file: FileData, index: number) => {
    const isImage = file.mime_type.startsWith('image/');

    if (isImage) {
      return (
        <div key={index} className="relative group flex-shrink-0">
          <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gunmetal-2 dark:to-charcoal-2 border border-blue-200/50 dark:border-charcoal/30 shadow-md hover:shadow-lg transition-all duration-300 transform hover:scale-105">
            <img
              src={file.url || `data:${file.mime_type};base64,${file.data}`}
              alt={file.filename}
              className="w-12 h-12 object-cover"
            />
            {/* Image Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <div className="absolute bottom-0.5 left-0.5 right-0.5">
                <div className="flex items-center gap-1 text-white text-[10px]">
                  <ImageIcon className="w-2 h-2" />
                  <span className="truncate font-medium">{file.filename}</span>
                </div>
              </div>
            </div>
            {/* Remove Button */}
            <button
              onClick={() => onRemoveFile(index)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onRemoveFile(index);
                }
              }}
              className="absolute -top-1 -right-1 bg-red-500 hover:bg-red-600 focus:bg-red-600 focus:ring-2 focus:ring-red-300 text-white rounded-full w-5 h-5 flex items-center justify-center transition-all duration-200 transform hover:scale-110 focus:scale-110 shadow-lg opacity-0 group-hover:opacity-100 focus:opacity-100"
              aria-label={`Remove ${file.filename}`}
              tabIndex={0}
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        </div>
      );
    } else {
      const colorScheme = getFileTypeColor(file.mime_type);
      const fileExtension = file.mime_type.split('/')[1]?.toUpperCase() || 'FILE';
      
      return (
        <div key={index} className="relative group flex-shrink-0">
          <div className={`flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gunmetal-2 dark:to-charcoal-2 border ${colorScheme.border} dark:border-charcoal/30 rounded-xl shadow-md hover:shadow-lg transition-all duration-300 transform hover:scale-105 min-w-0 max-w-44`}>
            {/* File Icon Container */}
            <div className={`flex-shrink-0 w-7 h-7 bg-gradient-to-br ${colorScheme.bg} rounded-lg flex items-center justify-center shadow-sm`}>
              <FileIcon mimeType={file.mime_type} className="w-4 h-4 text-white" />
            </div>
            
            {/* File Info */}
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-gray-800 dark:text-gray-200 truncate text-xs" title={file.filename}>
                {file.filename}
              </div>
              <div className="flex items-center gap-1 text-[10px] mt-0.5">
                <FileCheck className={`w-2 h-2 ${colorScheme.text} dark:text-gray-400`} />
                <span className={`font-medium ${colorScheme.text} dark:text-gray-400`}>{fileExtension}</span>
              </div>
            </div>

            {/* Remove Button */}
            <button
              onClick={() => onRemoveFile(index)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onRemoveFile(index);
                }
              }}
              className="flex-shrink-0 p-1 text-red-500 hover:text-red-700 focus:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 focus:bg-red-50 dark:focus:bg-red-900/20 focus:ring-2 focus:ring-red-200 dark:focus:ring-red-800 rounded-lg transition-all duration-200 opacity-0 group-hover:opacity-100 focus:opacity-100 transform hover:scale-110 focus:scale-110"
              aria-label={`Remove ${file.filename}`}
              tabIndex={0}
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        </div>
      );
    }
  };

  return (
    <div 
      className="file-preview-container bg-gradient-to-r from-blue-50/80 via-white to-purple-50/80 dark:from-gunmetal-2/80 dark:via-eerie-black dark:to-gunmetal-2/80 backdrop-blur-xl border-t border-blue-200/50 dark:border-charcoal/50 shadow-lg"
      role="region"
      aria-label="Selected files for upload"
    >
      <div className="max-w-4xl mx-auto px-4 py-3">
        {/* Live region for screen readers */}
        <div className="sr-only" aria-live="polite" aria-atomic="true">
          {files.length} file{files.length !== 1 ? 's' : ''} selected for upload
        </div>
        
        {/* Compact Header */}


        {/* Horizontal Scrolling Files */}
        <div 
          className="flex gap-2 overflow-x-auto pb-2 [&::-webkit-scrollbar]:hidden"
          role="list"
          aria-label="Selected files list"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {files.map((file, index) => (
            <div key={index} role="listitem">
              {renderFilePreview(file, index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
