import { useCallback } from 'react';
import { AppDispatch } from '../store';
import { FileData, Message } from '../chatSlice';
import { sendChatMessageStream, addMessage, createNewConversation, webSearch, generateImage, updateMessageText, addImageToHistory } from '../chatSlice';

interface UseChatHandlersProps {
  dispatch: AppDispatch;
  activeConversationId: string | null;
  input: string;
  selectedFiles: FileData[];
  setSelectedFiles: (files: FileData[]) => void;
  setInput: (value: string) => void;
}

export const useChatHandlers = ({
  dispatch,
  activeConversationId,
  input,
  selectedFiles,
  setSelectedFiles,
  setInput
}: UseChatHandlersProps) => {
  const handleSend = useCallback(async () => {
    if (!activeConversationId) {
      dispatch(createNewConversation());
      return;
    }

    if (input.trim() || selectedFiles.length > 0) {
      const userMessage: Message = {
        id: Date.now().toString(),
        sender: 'User',
        text: input,
        files: selectedFiles.length > 0 ? selectedFiles : undefined,
        timestamp: new Date().toISOString(),
      };

      dispatch(addMessage({ conversationId: activeConversationId, message: userMessage }));

      const messageToSend = input;
      const filesToSend = [...selectedFiles];
      setInput('');
      setSelectedFiles([]);

      try {
        await dispatch(sendChatMessageStream({
          message: messageToSend,
          files: filesToSend
        })).unwrap();
      } catch (error) {
        console.error('Failed to send message:', error);
      }
    }
  }, [dispatch, activeConversationId, input, selectedFiles, setInput, setSelectedFiles]);

  const handleSearch = useCallback(async () => {
    if (!input.trim() || !activeConversationId) return;

    dispatch(addMessage({
      conversationId: activeConversationId,
      message: {
        id: Date.now().toString(),
        sender: 'User',
        text: input,
        timestamp: new Date().toISOString(),
      },
    }));

    try {
      const results: string[] = await dispatch(webSearch({ query: input })).unwrap();
      const md = results.map((url, i) => `- [${url}](${url})`).join('\n');
      dispatch(addMessage({
        conversationId: activeConversationId,
        message: {
          id: (Date.now() + 1).toString(),
          sender: 'Bot',
          text: `**Search Results**\n\n${md}`,
          timestamp: new Date().toISOString(),
        },
      }));
    } catch (e) {
      console.error('Search failed:', e);
    } finally {
      setInput('');
    }
  }, [dispatch, activeConversationId, input, setInput]);

  const handleGenerateImage = useCallback(async () => {
    if (!input.trim() || !activeConversationId) return;

    // Add user message
    dispatch(addMessage({
      conversationId: activeConversationId,
      message: {
        id: Date.now().toString(),
        sender: 'User',
        text: input,
        timestamp: new Date().toISOString(),
      },
    }));

    // Add loading placeholder
    const loadingId = (Date.now() + 1).toString();
    dispatch(addMessage({
      conversationId: activeConversationId,
      message: {
        id: loadingId,
        sender: 'Bot',
        text: '🖼️ Generating image…',
        timestamp: new Date().toISOString(),
      },
    }));

    setInput('');

    try {
      const url: string = await dispatch(generateImage({ prompt: input })).unwrap();
      console.log('🖼️ generateImage payload →', url);

      dispatch(addImageToHistory({ prompt: input, url }));
      const markdown = `![Generated Image](${url})\n\n*Prompt: "${input}"*`;

      dispatch(updateMessageText({
        conversationId: activeConversationId,
        messageId: loadingId,
        newText: markdown,
      }));
    } catch (err: any) {
      console.error(err);
      dispatch(updateMessageText({
        conversationId: activeConversationId,
        messageId: loadingId,
        newText: `❌ Image generation failed: ${err.message}`,
      }));
    }
  }, [dispatch, activeConversationId, input, setInput]);

  return {
    handleSend,
    handleSearch,
    handleGenerateImage
  };
};
