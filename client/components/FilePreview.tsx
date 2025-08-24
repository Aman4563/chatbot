import React from 'react';
import { Paperclip, X } from 'lucide-react';
import { FileData } from '../chatSlice';
import { FileIcon } from './shared/FileIcon';

interface FilePreviewProps {
  files: FileData[];
  onRemoveFile: (index: number) => void;
}

export const FilePreview: React.FC<FilePreviewProps> = ({ files, onRemoveFile }) => {

  const renderFilePreview = (file: FileData, index: number) => {
    const isImage = file.mime_type.startsWith('image/');

    if (isImage) {
      return (
        <div key={index} className="relative inline-block m-1 group">
          <img
            src={file.url || `data:${file.mime_type};base64,${file.data}`}
            alt={file.filename}
            className="w-16 h-16 rounded-xl object-cover border border-gray-200 shadow-sm"
          />
          <button
            onClick={() => onRemoveFile(index)}
            className="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs transition-all duration-200 opacity-0 group-hover:opacity-100 shadow-lg"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      );
    } else {
      return (
        <div key={index} className="inline-flex items-center gap-2 m-1 px-3 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-xl text-sm relative group transition-all duration-200">
          <div className="flex items-center gap-2 text-gray-700">
            <FileIcon mimeType={file.mime_type} />
            <span className="truncate max-w-32 font-medium">{file.filename}</span>
          </div>
          <button
            onClick={() => onRemoveFile(index)}
            className="ml-2 text-red-500 hover:text-red-700 transition-colors duration-200 opacity-0 group-hover:opacity-100"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      );
    }
  };

  return (
    <div className="bg-white/95 backdrop-blur-sm border-t border-gray-200 shadow-lg">
      <div className="max-w-4xl mx-auto px-6 py-4">
        <div className="flex items-center gap-3 text-sm text-gray-600 mb-4">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
            <Paperclip className="w-4 h-4 text-blue-600" />
          </div>
          <span className="font-semibold">Selected files ({files.length}):</span>
        </div>
        <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto custom-scrollbar">
          {files.map((file, index) => renderFilePreview(file, index))}
        </div>
      </div>
    </div>
  );
};
