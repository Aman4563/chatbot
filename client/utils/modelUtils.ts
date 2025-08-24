import { Zap, Brain, Bot, Eye } from 'lucide-react';

export interface ModelProvider {
  name: string;
  color: string;
  icon: typeof Bot;
}

/**
 * Get provider information based on model name
 */
export const getModelProvider = (model: string): ModelProvider => {
  if (model.includes('gpt')) {
    return { name: 'OpenAI', color: 'from-green-500 to-emerald-600', icon: Brain };
  }
  if (model.includes('claude')) {
    return { name: 'Anthropic', color: 'from-orange-500 to-red-600', icon: Bot };
  }
  if (model.includes('gemini')) {
    return { name: 'Google', color: 'from-blue-500 to-indigo-600', icon: Eye };
  }
  if (model.includes('mistral')) {
    return { name: 'Mistral AI', color: 'from-purple-500 to-pink-600', icon: Zap };
  }
  return { name: 'AI', color: 'from-gray-500 to-gray-600', icon: Bot };
};

/**
 * Get provider icon component based on provider name
 */
export const getProviderIcon = (provider: string) => {
  switch (provider.toLowerCase()) {
    case 'mistral':
      return Zap;
    case 'openai':
      return Brain;
    case 'anthropic':
      return Bot;
    case 'google':
      return Eye;
    default:
      return Bot;
  }
};

/**
 * Get provider color class based on provider name
 */
export const getProviderColor = (provider: string): string => {
  switch (provider.toLowerCase()) {
    case 'mistral':
      return 'text-orange-500';
    case 'openai':
      return 'text-green-500';
    case 'anthropic':
      return 'text-purple-500';
    case 'google':
      return 'text-blue-500';
    default:
      return 'text-gray-500';
  }
};
