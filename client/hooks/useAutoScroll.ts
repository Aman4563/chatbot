import { useEffect, RefObject } from 'react';
import { Conversation } from '../chatSlice';
import { CHAT_CONSTANTS } from '../constants/chatConstants';

interface UseAutoScrollProps {
  messagesEndRef: RefObject<HTMLDivElement>;
  activeConversationId: string | null;
  conversations: Conversation[];
}

export const useAutoScroll = ({
  messagesEndRef,
  activeConversationId,
  conversations
}: UseAutoScrollProps) => {
  useEffect(() => {
    if (!conversations?.length || !activeConversationId) return;
    
    const activeConversation = conversations.find(conv => conv.id === activeConversationId);
    if (activeConversation?.messages?.length) {
      messagesEndRef.current?.scrollIntoView({ behavior: CHAT_CONSTANTS.SCROLL_BEHAVIOR });
    }
  }, [activeConversationId, conversations, messagesEndRef]);
};
