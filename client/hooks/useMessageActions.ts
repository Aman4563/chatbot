import { useCallback } from 'react';
import { AppDispatch } from '../store';
import { Conversation, navigateUserEditVersion, setUserBranchIndex, replaceConversationTail, navigateResponseVersion, regenerateResponse } from '../chatSlice';
import { CHAT_CONSTANTS } from '../constants/chatConstants';

interface UseMessageActionsProps {
  dispatch: AppDispatch;
  conversations: Conversation[];
  activeConversationId: string | null;
  setCopiedCode: (code: string) => void;
  setCollapsedBlocks: React.Dispatch<React.SetStateAction<Set<string>>>;
  setCopiedChat: (copied: boolean) => void;
}

export const useMessageActions = ({
  dispatch,
  conversations,
  activeConversationId,
  setCopiedCode,
  setCollapsedBlocks,
  setCopiedChat
}: UseMessageActionsProps) => {
  const handleNavigateUserEdit = useCallback((messageId: string, direction: 'prev' | 'next') => {
    // Early returns for invalid states
    if (!conversations?.length || !activeConversationId) return;
    
    const conv = conversations.find(c => c.id === activeConversationId);
    if (!conv) return;

    const userMsg = conv.messages.find(m => m.id === messageId && m.sender === 'User');
    if (!userMsg) return;

    // Priority 1: Handle edits (different versions of the same message text)
    if (userMsg.edits && userMsg.edits.length > 1) {
      const currentEdit = userMsg.currentEditIndex ?? (userMsg.edits.length - 1);
      let newEdit = direction === 'prev' ? currentEdit - 1 : currentEdit + 1;
      
      // Ensure we stay within bounds
      newEdit = Math.max(0, Math.min(userMsg.edits.length - 1, newEdit));
      
      // Only navigate if we can actually move
      if (newEdit !== currentEdit) {
        dispatch(navigateUserEditVersion({ messageId, direction }));
      }
    }
    // Priority 2: Handle branches (different conversation paths)
    else if (userMsg.branches && userMsg.branches.length > 1) {
      const currentBranch = userMsg.currentBranchIndex ?? 0;
      let newBranch = direction === 'prev' ? currentBranch - 1 : currentBranch + 1;
      
      // Ensure we stay within bounds
      newBranch = Math.max(0, Math.min(userMsg.branches.length - 1, newBranch));
      
      // Only navigate if we can actually move
      if (newBranch !== currentBranch) {
        dispatch(setUserBranchIndex({ messageId, branchIndex: newBranch }));
        
        // Find the message index for tail replacement
        const msgIndex = conv.messages.findIndex(m => m.id === messageId);
        if (msgIndex >= 0) {
          const head = conv.messages.slice(0, msgIndex + 1);
          const tail = userMsg.branches[newBranch] || [];
          dispatch(replaceConversationTail({
            conversationId: activeConversationId!,
            head,
            tail
          }));
        }
      }
    }
  }, [dispatch, conversations, activeConversationId]);

  const handleNavigateResponse = useCallback((messageId: string, direction: 'prev' | 'next') => {
    dispatch(navigateResponseVersion({ messageId, direction }));
  }, [dispatch]);

  const handleRegenerateResponse = useCallback(async (messageId: string) => {
    try {
      await dispatch(regenerateResponse(messageId)).unwrap();
    } catch (error) {
      console.error('Failed to regenerate response:', error);
    }
  }, [dispatch]);

  const copyToClipboard = useCallback(async (text: string, blockId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCode(blockId);
      setTimeout(() => setCopiedCode(''), CHAT_CONSTANTS.COPY_TIMEOUT);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  }, [setCopiedCode]);

  const toggleCodeBlock = useCallback((blockId: string) => {
    setCollapsedBlocks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(blockId)) {
        newSet.delete(blockId);
      } else {
        newSet.add(blockId);
      }
      return newSet;
    });
  }, [setCollapsedBlocks]);

  const copyChatAsMarkdown = useCallback(async () => {
    if (!conversations?.length || !activeConversationId) return;
    
    const activeConversation = conversations.find(conv => conv.id === activeConversationId);
    if (!activeConversation?.messages?.length) return;

    const chatMarkdown = activeConversation.messages.map(msg => {
      const sender = msg.sender === 'User' ? '**You**' : '**Xbot**';
      const timestamp = new Date(msg.timestamp).toLocaleString();
      let content = `${sender} (${timestamp}):\n\n${msg.text || ''}`;

      if (msg.files && msg.files.length > 0) {
        content += '\n\n*Attachments:*\n';
        msg.files.forEach(file => {
          content += `- ${file.filename} (${file.mime_type})\n`;
        });
      }

      return content;
    }).join('\n\n---\n\n');

    try {
      await navigator.clipboard.writeText(chatMarkdown);
      setCopiedChat(true);
      setTimeout(() => setCopiedChat(false), CHAT_CONSTANTS.COPY_TIMEOUT);
    } catch (err) {
      console.error('Failed to copy chat: ', err);
    }
  }, [conversations, activeConversationId, setCopiedChat]);

  return {
    handleNavigateUserEdit,
    handleNavigateResponse,
    handleRegenerateResponse,
    copyToClipboard,
    toggleCodeBlock,
    copyChatAsMarkdown
  };
};
