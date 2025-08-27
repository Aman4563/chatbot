import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../store';
import {
  setWebsiteTheme,
  setCodeBlockTheme,
  setShowLineNumbers,
  setShowLanguageBadge,
  setAutoWrapCode,
  setFontSize,
  setCompactMode,
  setAutoScroll,
  setShowTypingIndicator,
} from '../settingsSlice';
import { Settings as SettingsIcon, X, Palette, Code, Monitor, MessageSquare } from 'lucide-react';

interface SettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Settings: React.FC<SettingsProps> = ({ isOpen, onClose }) => {
  const dispatch = useDispatch<AppDispatch>();
  const settings = useSelector((state: RootState) => state.settings);

  const [activeTab, setActiveTab] = useState<'appearance' | 'code' | 'chat'>('appearance');

  const codeBlockThemes = [
    { value: 'dracula', label: 'Dracula', preview: 'bg-purple-900' },
    { value: 'monokai', label: 'Monokai', preview: 'bg-gray-900' },
    { value: 'one-dark-pro', label: 'One Dark Pro', preview: 'bg-gray-800' },
    { value: 'tokyo-night', label: 'Tokyo Night', preview: 'bg-blue-900' },
    { value: 'nord', label: 'Nord', preview: 'bg-slate-800' },
    { value: 'github-dark', label: 'GitHub Dark', preview: 'bg-gray-900' },
    { value: 'github-light', label: 'GitHub Light', preview: 'bg-gray-100' },
  ];

  const fontSizes = [
    { value: 'small', label: 'Small', size: 'text-sm' },
    { value: 'medium', label: 'Medium', size: 'text-base' },
    { value: 'large', label: 'Large', size: 'text-lg' },
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-gray-900">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <SettingsIcon className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('appearance')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'appearance'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            <Palette className="h-4 w-4" />
            Appearance
          </button>
          <button
            onClick={() => setActiveTab('code')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'code'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            <Code className="h-4 w-4" />
            Code Blocks
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'chat'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            Chat
          </button>
        </div>

        {/* Content */}
        <div className="max-h-[60vh] overflow-y-auto p-6">
          {activeTab === 'appearance' && (
            <div className="space-y-6">
              {/* Website Theme */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Website Theme
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {(['light', 'dark', 'auto'] as const).map((theme) => (
                    <button
                      key={theme}
                      onClick={() => dispatch(setWebsiteTheme(theme))}
                      className={`flex items-center justify-center gap-2 rounded-lg border-2 p-3 text-sm font-medium transition-colors ${
                        settings.websiteTheme === theme
                          ? 'border-blue-600 bg-blue-50 text-blue-600 dark:bg-blue-900/20'
                          : 'border-gray-200 text-gray-700 hover:border-gray-300 dark:border-gray-600 dark:text-gray-300 dark:hover:border-gray-500'
                      }`}
                    >
                      <Monitor className="h-4 w-4" />
                      {theme.charAt(0).toUpperCase() + theme.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Font Size */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Font Size
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {fontSizes.map((size) => (
                    <button
                      key={size.value}
                      onClick={() => dispatch(setFontSize(size.value))}
                      className={`flex items-center justify-center gap-2 rounded-lg border-2 p-3 text-sm font-medium transition-colors ${
                        settings.fontSize === size.value
                          ? 'border-blue-600 bg-blue-50 text-blue-600 dark:bg-blue-900/20'
                          : 'border-gray-200 text-gray-700 hover:border-gray-300 dark:border-gray-600 dark:text-gray-300 dark:hover:border-gray-500'
                      }`}
                    >
                      <span className={size.size}>Aa</span>
                      {size.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Compact Mode */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Compact Mode
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Reduce spacing for more content
                  </p>
                </div>
                <button
                  onClick={() => dispatch(setCompactMode(!settings.compactMode))}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.compactMode ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.compactMode ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          )}

          {activeTab === 'code' && (
            <div className="space-y-6">
              {/* Code Block Theme */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Code Block Theme
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {codeBlockThemes.map((theme) => (
                    <button
                      key={theme.value}
                      onClick={() => dispatch(setCodeBlockTheme(theme.value))}
                      className={`flex items-center justify-between rounded-lg border-2 p-3 text-sm font-medium transition-colors ${
                        settings.codeBlockTheme === theme.value
                          ? 'border-blue-600 bg-blue-50 text-blue-600 dark:bg-blue-900/20'
                          : 'border-gray-200 text-gray-700 hover:border-gray-300 dark:border-gray-600 dark:text-gray-300 dark:hover:border-gray-500'
                      }`}
                    >
                      <span>{theme.label}</span>
                      <div className={`h-4 w-4 rounded ${theme.preview}`} />
                    </button>
                  ))}
                </div>
              </div>

              {/* Code Block Options */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Show Line Numbers
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Display line numbers in code blocks
                    </p>
                  </div>
                  <button
                    onClick={() => dispatch(setShowLineNumbers(!settings.showLineNumbers))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.showLineNumbers ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.showLineNumbers ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Show Language Badge
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Display language name in code block header
                    </p>
                  </div>
                  <button
                    onClick={() => dispatch(setShowLanguageBadge(!settings.showLanguageBadge))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.showLanguageBadge ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.showLanguageBadge ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Auto Wrap Code
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Automatically wrap long lines in code blocks
                    </p>
                  </div>
                  <button
                    onClick={() => dispatch(setAutoWrapCode(!settings.autoWrapCode))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.autoWrapCode ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.autoWrapCode ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'chat' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Auto Scroll
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Automatically scroll to new messages
                  </p>
                </div>
                <button
                  onClick={() => dispatch(setAutoScroll(!settings.autoScroll))}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.autoScroll ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.autoScroll ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Show Typing Indicator
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Display typing indicator when AI is responding
                  </p>
                </div>
                <button
                  onClick={() => dispatch(setShowTypingIndicator(!settings.showTypingIndicator))}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.showTypingIndicator ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.showTypingIndicator ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 dark:border-gray-700">
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};