import { useCallback } from 'react';
import { FileData } from '../chatSlice';
import { CHAT_CONSTANTS } from '../constants/chatConstants';

interface UseFileHandlersProps {
  setSelectedFiles: React.Dispatch<React.SetStateAction<FileData[]>>;
  setDragOver: React.Dispatch<React.SetStateAction<boolean>>;
}

export const useFileHandlers = ({
  setSelectedFiles,
  setDragOver
}: UseFileHandlersProps) => {
  const validateAndProcessFile = useCallback(async (file: File): Promise<FileData | null> => {
    // Validate file size
    if (file.size > CHAT_CONSTANTS.MAX_FILE_SIZE) {
      alert(`File ${file.name} is too large. Maximum size is ${Math.round(CHAT_CONSTANTS.MAX_FILE_SIZE / 1024 / 1024)}MB.`);
      return null;
    }

    // Validate file type
    if (!CHAT_CONSTANTS.ALLOWED_FILE_TYPES.includes(file.type)) {
      alert(`File type ${file.type} is not supported.`);
      return null;
    }

    try {
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsDataURL(file);
      });

      return {
        data: base64.split(',')[1],
        mime_type: file.type,
        filename: file.name,
        url: base64
      };
    } catch (error) {
      console.error('Error processing file:', error);
      alert(`Failed to process file ${file.name}`);
      return null;
    }
  }, []);

  const handleFileSelect = useCallback(async (files: FileList) => {
    const fileDataArray: FileData[] = [];

    for (const file of Array.from(files)) {
      const fileData = await validateAndProcessFile(file);
      if (fileData) {
        fileDataArray.push(fileData);
      }
    }

    setSelectedFiles(prev => [...prev, ...fileDataArray]);
  }, [validateAndProcessFile, setSelectedFiles]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  }, [handleFileSelect, setDragOver]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, [setDragOver]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, [setDragOver]);

  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  }, [setSelectedFiles]);

  return {
    handleFileSelect,
    handleDrop,
    handleDragOver,
    handleDragLeave,
    removeFile
  };
};
