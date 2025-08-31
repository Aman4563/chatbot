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
import { Settings as SettingsIcon, X, Palette, Code, Monitor, MessageSquare, Download, Check } from 'lucide-react';

interface SettingsProps {
  isOpen: boolean;
  onClose: () => void;
  onCopyChat?: () => void;
  copiedChat?: boolean;
}

// Custom Toggle Switch Component
const CustomToggle: React.FC<{
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}> = ({ checked, onChange, disabled = false }) => {
  return (
    <div className="custom-toggle-container">
      <button
        onClick={() => !disabled && onChange(!checked)}
        disabled={disabled}
        className={`
          relative inline-flex h-5 w-9 sm:h-6 sm:w-11 items-center rounded-full 
          transition-all duration-300 ease-in-out transform hover:scale-105 
          focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500/20
          shadow-lg hover:shadow-xl touch-target
          ${checked 
            ? 'bg-gradient-to-r from-blue-500 via-blue-600 to-purple-600 shadow-blue-500/30' 
            : 'bg-gradient-to-r from-gray-200 via-gray-300 to-gray-400 dark:from-gray-700 dark:via-gray-600 dark:to-gray-500 shadow-gray-300/30 dark:shadow-gray-600/30'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        style={{
          boxShadow: checked 
            ? '0 4px 14px 0 rgba(59, 130, 246, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2)' 
            : '0 2px 8px 0 rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
        }}
        aria-label={`Toggle ${checked ? 'on' : 'off'}`}
      >
        {/* Toggle Circle */}
        <span
          className={`
            inline-block h-3.5 w-3.5 sm:h-4 sm:w-4 transform rounded-full 
            transition-all duration-300 ease-in-out relative overflow-hidden
            ${checked 
              ? 'translate-x-5 sm:translate-x-6 bg-white shadow-lg' 
              : 'translate-x-0.5 bg-white shadow-md'
            }
          `}
          style={{
            boxShadow: checked 
              ? '0 2px 8px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.05)' 
              : '0 1px 4px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(255, 255, 255, 0.05)'
          }}
        >
          {/* Inner glow when active */}
          {checked && (
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 opacity-60 animate-pulse" />
          )}
        </span>
        
        {/* Background pattern */}
        <div className={`
          absolute inset-0 rounded-full opacity-10 pointer-events-none
          ${checked 
            ? 'bg-[radial-gradient(circle_at_30%_30%,_rgba(255,255,255,0.3)_0%,_transparent_50%)]' 
            : 'bg-[radial-gradient(circle_at_70%_70%,_rgba(0,0,0,0.1)_0%,_transparent_50%)]'
          }
        `} />
      </button>
    </div>
  );
};

export const Settings: React.FC<SettingsProps> = ({ isOpen, onClose, onCopyChat, copiedChat }) => {
  const dispatch = useDispatch<AppDispatch>();
  const settings = useSelector((state: RootState) => state.settings);

  const [activeTab, setActiveTab] = useState<'appearance' | 'code' | 'chat' | 'export'>('appearance');

  const codeBlockThemes = [
    { value: 'dracula', label: 'Dracula', preview: 'bg-purple-900' },
    { value: 'monokai', label: 'Monokai', preview: 'bg-gray-900' },
    { value: 'one-dark-pro', label: 'One Dark Pro', preview: 'bg-gray-800' },
    { value: 'tokyo-night', label: 'Tokyo Night', preview: 'bg-blue-900' },
    { value: 'nord', label: 'Nord', preview: 'bg-slate-800' },
    { value: 'github-dark', label: 'GitHub Dark', preview: 'bg-gray-900' },
    { value: 'github-light', label: 'GitHub Light', preview: 'bg-gray-100' },
  ];

  const fontSizes: Array<{ value: 'small' | 'medium' | 'large'; label: string; size: string }> = [
    { value: 'small', label: 'Small', size: 'text-sm' },
    { value: 'medium', label: 'Medium', size: 'text-base' },
    { value: 'large', label: 'Large', size: 'text-lg' },
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center settings-overlay p-4">
      <div className="w-full max-w-2xl max-h-[90vh] md:max-h-[90vh] overflow-hidden rounded-2xl settings-modal shadow-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b settings-header-border px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center gap-2 sm:gap-3">
            <SettingsIcon className="h-5 w-5 sm:h-6 sm:w-6 settings-icon" />
            <h2 className="text-lg sm:text-xl font-semibold settings-title">Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 sm:p-2 settings-close-button touch-target"
          >
            <X className="h-4 w-4 sm:h-5 sm:w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b settings-tabs-border overflow-x-auto">
          <button
            onClick={() => setActiveTab('appearance')}
            className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-6 py-2 sm:py-3 text-xs sm:text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === 'appearance'
                ? 'settings-tab-active'
                : 'settings-tab-inactive'
            }`}
          >
            <Palette className="h-3 w-3 sm:h-4 sm:w-4" />
            <span className="hidden xs:inline">Appearance</span>
            <span className="xs:hidden">Theme</span>
          </button>
          <button
            onClick={() => setActiveTab('code')}
            className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-6 py-2 sm:py-3 text-xs sm:text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === 'code'
                ? 'settings-tab-active'
                : 'settings-tab-inactive'
            }`}
          >
            <Code className="h-3 w-3 sm:h-4 sm:w-4" />
            Code
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-6 py-2 sm:py-3 text-xs sm:text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === 'chat'
                ? 'settings-tab-active'
                : 'settings-tab-inactive'
            }`}
          >
            <MessageSquare className="h-3 w-3 sm:h-4 sm:w-4" />
            Chat
          </button>
          <button
            onClick={() => setActiveTab('export')}
            className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-6 py-2 sm:py-3 text-xs sm:text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === 'export'
                ? 'settings-tab-active'
                : 'settings-tab-inactive'
            }`}
          >
            <Download className="h-3 w-3 sm:h-4 sm:w-4" />
            Export
          </button>
        </div>

        {/* Content */}
        <div className="max-h-[60vh] overflow-y-auto p-3 sm:p-6">
          {activeTab === 'appearance' && (
            <div className="space-y-6">
              {/* Website Theme */}
              <div>
                <label className="block text-sm font-medium settings-label mb-3">
                  Website Theme
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {(['light', 'dark', 'auto'] as const).map((theme) => (
                    <button
                      key={theme}
                      onClick={() => dispatch(setWebsiteTheme(theme))}
                      className={`flex items-center justify-center gap-1 sm:gap-2 rounded-lg border-2 p-2 sm:p-3 text-xs sm:text-sm font-medium transition-colors ${
                        settings.websiteTheme === theme
                          ? 'settings-option-active'
                          : 'settings-option-inactive'
                      }`}
                    >
                      <Monitor className="h-3 w-3 sm:h-4 sm:w-4" />
                      {theme.charAt(0).toUpperCase() + theme.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Font Size */}
              <div>
                <label className="block text-sm font-medium settings-label mb-3">
                  Font Size
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {fontSizes.map((size) => (
                    <button
                      key={size.value}
                      onClick={() => dispatch(setFontSize(size.value))}
                      className={`flex items-center justify-center gap-1 sm:gap-2 rounded-lg border-2 p-2 sm:p-3 text-xs sm:text-sm font-medium transition-colors ${
                        settings.fontSize === size.value
                          ? 'settings-option-active'
                          : 'settings-option-inactive'
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
                  <label className="text-sm font-medium settings-label">
                    Compact Mode
                  </label>
                  <p className="text-xs settings-description">
                    Reduce spacing for more content
                  </p>
                </div>
                <CustomToggle
                  checked={settings.compactMode}
                  onChange={(checked) => dispatch(setCompactMode(checked))}
                />
              </div>
            </div>
          )}

          {activeTab === 'code' && (
            <div className="space-y-6">
              {/* Code Block Theme */}
              <div>
                <label className="block text-sm font-medium settings-label mb-3">
                  Code Block Theme
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {codeBlockThemes.map((theme) => (
                    <button
                      key={theme.value}
                      onClick={() => dispatch(setCodeBlockTheme(theme.value))}
                      className={`flex items-center justify-between rounded-lg border-2 p-2 sm:p-3 text-xs sm:text-sm font-medium transition-colors ${
                        settings.codeBlockTheme === theme.value
                          ? 'settings-option-active'
                          : 'settings-option-inactive'
                      }`}
                    >
                      <span>{theme.label}</span>
                      <div className={`h-3 w-3 sm:h-4 sm:w-4 rounded ${theme.preview}`} />
                    </button>
                  ))}
                </div>
              </div>

              {/* Code Block Options */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium settings-label">
                      Show Line Numbers
                    </label>
                    <p className="text-xs settings-description">
                      Display line numbers in code blocks
                    </p>
                  </div>
                  <CustomToggle
                    checked={settings.showLineNumbers}
                    onChange={(checked) => dispatch(setShowLineNumbers(checked))}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium settings-label">
                      Show Language Badge
                    </label>
                    <p className="text-xs settings-description">
                      Display language name in code block header
                    </p>
                  </div>
                  <CustomToggle
                    checked={settings.showLanguageBadge}
                    onChange={(checked) => dispatch(setShowLanguageBadge(checked))}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium settings-label">
                      Auto Wrap Code
                    </label>
                    <p className="text-xs settings-description">
                      Automatically wrap long lines in code blocks
                    </p>
                  </div>
                  <CustomToggle
                    checked={settings.autoWrapCode}
                    onChange={(checked) => dispatch(setAutoWrapCode(checked))}
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'chat' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium settings-label">
                    Auto Scroll
                  </label>
                  <p className="text-xs settings-description">
                    Automatically scroll to new messages
                  </p>
                </div>
                <CustomToggle
                  checked={settings.autoScroll}
                  onChange={(checked) => dispatch(setAutoScroll(checked))}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium settings-label">
                    Show Typing Indicator
                  </label>
                  <p className="text-xs settings-description">
                    Display typing indicator when AI is responding
                  </p>
                </div>
                <CustomToggle
                  checked={settings.showTypingIndicator}
                  onChange={(checked) => dispatch(setShowTypingIndicator(checked))}
                />
              </div>
            </div>
          )}

          {activeTab === 'export' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold settings-title mb-4">Export Chat</h3>
                <p className="text-sm settings-description mb-6">
                  Export your current conversation as a markdown file to save or share.
                </p>
                
                <div className="flex items-center justify-between p-4 border settings-option-inactive-border rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <Download className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h4 className="font-medium settings-label">Chat as Markdown</h4>
                      <p className="text-xs settings-description">
                        Export conversation with formatting preserved
                      </p>
                    </div>
                  </div>
                  
                  {onCopyChat && (
                <button
                      onClick={onCopyChat}
                      className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-sm hover:shadow-md"
                    >
                      {copiedChat ? (
                        <>
                          <Check className="w-4 h-4" />
                          <span className="text-sm font-medium">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Download className="w-4 h-4" />
                          <span className="text-sm font-medium">Export</span>
                        </>
                      )}
                </button>
                  )}
                </div>
                
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200/50 dark:border-blue-800/50 rounded-xl p-4">
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 bg-blue-100 dark:bg-blue-800 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <MessageSquare className="w-3 h-3 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h5 className="font-medium text-blue-900 dark:text-blue-100 mb-1">Export Tips</h5>
                      <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                        <li>• Exported content includes message formatting and code blocks</li>
                        <li>• Copy the content and paste it into any markdown editor</li>
                        <li>• Perfect for sharing conversations or creating documentation</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t settings-header-border px-3 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-end gap-2 sm:gap-3">
            <button
              onClick={onClose}
              className="rounded-lg px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium settings-label hover:bg-gray-100 dark:hover:bg-gray-800 touch-target"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};