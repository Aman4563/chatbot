import { 
  ImageIcon, 
  FileText, 
  File, 
  FileSpreadsheet, 
  FileVideo, 
  FileAudio, 
  FileCode,
  FileArchive,
  Database,
  Presentation
} from 'lucide-react';

/**
 * Get the appropriate icon component for a file based on its MIME type
 */
export const getFileIcon = (mimeType: string) => {
  // Image files
  if (mimeType.startsWith('image/')) return ImageIcon;
  
  // Document files
  if (mimeType.includes('pdf')) return FileText;
  if (mimeType.includes('word') || mimeType.includes('document')) return FileText;
  if (mimeType.includes('text/')) return FileText;
  
  // Spreadsheet files
  if (mimeType.includes('spreadsheet') || mimeType.includes('excel') || mimeType.includes('csv')) return FileSpreadsheet;
  
  // Presentation files
  if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) return Presentation;
  
  // Video files
  if (mimeType.startsWith('video/')) return FileVideo;
  
  // Audio files
  if (mimeType.startsWith('audio/')) return FileAudio;
  
  // Code files
  if (mimeType.includes('javascript') || mimeType.includes('json') || 
      mimeType.includes('xml') || mimeType.includes('html') || 
      mimeType.includes('css') || mimeType.includes('text/plain') ||
      mimeType.includes('text/x-python') || mimeType.includes('text/markdown')) return FileCode;
  
  // Archive files
  if (mimeType.includes('zip') || mimeType.includes('rar') || 
      mimeType.includes('tar') || mimeType.includes('gzip')) return FileArchive;
  
  // Database files
  if (mimeType.includes('database') || mimeType.includes('sql')) return Database;
  
  // Default
  return File;
};

/**
 * Get color scheme for file type
 */
export const getFileTypeColor = (mimeType: string): { bg: string; text: string; border: string } => {
  if (mimeType.startsWith('image/')) 
    return { bg: 'from-green-500 to-emerald-600', text: 'text-green-600', border: 'border-green-200' };
  
  if (mimeType.includes('pdf')) 
    return { bg: 'from-red-500 to-rose-600', text: 'text-red-600', border: 'border-red-200' };
    
  if (mimeType.includes('word') || mimeType.includes('document') || mimeType.includes('text/')) 
    return { bg: 'from-blue-500 to-blue-600', text: 'text-blue-600', border: 'border-blue-200' };
    
  if (mimeType.includes('spreadsheet') || mimeType.includes('excel') || mimeType.includes('csv')) 
    return { bg: 'from-emerald-500 to-teal-600', text: 'text-emerald-600', border: 'border-emerald-200' };
    
  if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) 
    return { bg: 'from-orange-500 to-amber-600', text: 'text-orange-600', border: 'border-orange-200' };
    
  if (mimeType.startsWith('video/')) 
    return { bg: 'from-purple-500 to-violet-600', text: 'text-purple-600', border: 'border-purple-200' };
    
  if (mimeType.startsWith('audio/')) 
    return { bg: 'from-pink-500 to-rose-600', text: 'text-pink-600', border: 'border-pink-200' };
    
  if (mimeType.includes('javascript') || mimeType.includes('json') || 
      mimeType.includes('xml') || mimeType.includes('html') || 
      mimeType.includes('css') || mimeType.includes('text/x-python') || 
      mimeType.includes('text/markdown')) 
    return { bg: 'from-yellow-500 to-amber-600', text: 'text-yellow-600', border: 'border-yellow-200' };
    
  if (mimeType.includes('zip') || mimeType.includes('rar') || 
      mimeType.includes('tar') || mimeType.includes('gzip')) 
    return { bg: 'from-gray-500 to-slate-600', text: 'text-gray-600', border: 'border-gray-200' };
    
  // Default
  return { bg: 'from-blue-500 to-indigo-600', text: 'text-blue-600', border: 'border-blue-200' };
};

/**
 * Format file size in a human-readable format
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Check if a file type is allowed based on MIME type
 */
export const isFileTypeAllowed = (mimeType: string, allowedTypes: string[]): boolean => {
  return allowedTypes.includes(mimeType);
};

/**
 * Extract file extension from filename
 */
export const getFileExtension = (filename: string): string => {
  return filename.split('.').pop()?.toLowerCase() || '';
};
