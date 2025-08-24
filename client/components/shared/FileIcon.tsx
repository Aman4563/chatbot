import React from 'react';
import { getFileIcon } from '../../utils/fileUtils';

interface FileIconProps {
  mimeType: string;
  className?: string;
}

export const FileIcon: React.FC<FileIconProps> = ({ mimeType, className = "w-4 h-4" }) => {
  const IconComponent = getFileIcon(mimeType);
  return <IconComponent className={className} />;
};
