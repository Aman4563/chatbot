// File size constants
const MB = 1024 * 1024;

export const CHAT_CONSTANTS = {
  // File handling
  MAX_FILE_SIZE: 10 * MB, // 10MB
  ALLOWED_FILE_TYPES: [
    // Images - expanded to match backend
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 'image/tiff',
    // Text files - expanded to match backend
    'text/plain', 'text/csv', 'text/markdown', 'text/xml', 'application/json', 'application/xml',
    // Documents - expanded to include Excel and PowerPoint
    'application/pdf', 
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    // Programming files - new support
    'text/x-python', 'application/javascript', 'text/html', 'text/css'
  ] as const,
  
  // UI constants
  COPY_TIMEOUT: 2000,
  MAX_INPUT_HEIGHT: 144, // 36 * 4 lines
  MIN_INPUT_HEIGHT: 52,
  
  // Code block
  CODE_COLLAPSE_THRESHOLD: 10, // lines
  
  // Animation durations (milliseconds)
  TRANSITION_DURATION: 200,
  HOVER_TRANSITION: 300,
  
  // Scroll behavior
  SCROLL_BEHAVIOR: 'smooth' as ScrollBehavior,
  
  // Tool types
  TOOL_TYPES: ['chat', 'search', 'image'] as const,
  
  // Message types
  MESSAGE_SENDERS: {
    USER: 'User',
    BOT: 'Bot'
  } as const,
  
  // Navigation directions
  NAVIGATION_DIRECTIONS: {
    PREV: 'prev',
    NEXT: 'next'
  } as const
} as const;

// Type exports for better type safety
export type ToolType = typeof CHAT_CONSTANTS.TOOL_TYPES[number];
export type MessageSender = typeof CHAT_CONSTANTS.MESSAGE_SENDERS[keyof typeof CHAT_CONSTANTS.MESSAGE_SENDERS];
export type NavigationDirection = typeof CHAT_CONSTANTS.NAVIGATION_DIRECTIONS[keyof typeof CHAT_CONSTANTS.NAVIGATION_DIRECTIONS];
