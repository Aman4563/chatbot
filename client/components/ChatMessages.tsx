import React, { RefObject, useEffect, useMemo, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Check,
  Edit3,
  RotateCcw,
  User,
  Bot,
  MessageCircle,
  X,
  FileText,
  Image as ImageIcon
} from 'lucide-react';
import { Conversation, Message, FileData } from '../chatSlice';
import { CHAT_CONSTANTS } from '../constants/chatConstants';
// import { MarkdownRenderer } from './shared/MarkdownRenderer';
import { FileIcon } from './shared/FileIcon';
import { Streamdown } from 'streamdown';

import { codeToHtml } from "shiki";
import {
  transformerNotationDiff,
  transformerNotationHighlight,
  transformerNotationFocus,
  transformerMetaHighlight,
} from "@shikijs/transformers";
import { LLMCodeBlock } from "./shared/LLMCodeBlock";



import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

// If you use images in markdown, keep your original helper. Adjust the path if needed.
import { ImageWithHistory } from '.././Component/ImageWithHistory';

/* ───────────────────────── helpers ───────────────────────── */

// stable (deterministic) id for a code block based on its contents
function hashString(input: string) {
  let h = 0;
  for (let i = 0; i < input.length; i++) {
    h = (h << 5) - h + input.charCodeAt(i);
    h |= 0;
  }
  return `code-${Math.abs(h)}`;
}

// Extract plain text out of any React children tree
function extractText(node: any): string {
  if (node == null) return '';
  if (typeof node === 'string') return node;
  if (Array.isArray(node)) return node.map(extractText).join('');
  if (React.isValidElement(node)) return extractText((node as any).props?.children);
  return '';
}


// function CodeBlock({ className, children }: any) {
//   const lang = className?.replace("language-", "") || "txt";
//   const code = String(children ?? "");
//   const [html, setHtml] = useState<string>("");

//   useEffect(() => {
//     codeToHtml(code, {
//       lang,
//       theme: "github-dark",
//       transformers: [transformerNotationDiff(), transformerMetaHighlight()],
//     }).then(setHtml);
//   }, [code, lang]);

//   return <div dangerouslySetInnerHTML={{ __html: html }} />;
// }


// Call this on the streamed markdown before rendering
// lib/normalizeFences.ts
export function normalizeFences(md: string) {
  const lines = md.split(/\r?\n/);
  let open = false;
  const out: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    const t = lines[i].trim();
    const isFence = /^`{3,}/.test(t);
    if (isFence) {
      if (open) {
        out.push(lines[i]);
        open = false;
        // Drop an immediate duplicate closing fence (common LLM artifact)
        if (i + 1 < lines.length && /^`{3,}$/.test(lines[i + 1].trim())) i++;
      } else {
        open = true;
        out.push(lines[i]);
      }
      continue;
    }
    out.push(lines[i]);
  }
  return out.join("\n");
}




/**
 * Auto-convert common “plain text” math to LaTeX so KaTeX renders it nicely.
 * This is intentionally conservative and targets the exact shapes from your screenshots:
 *  - σ(x) = 1 / (1 + e<sup>-x</sup>)
 *  - f(x) = (1 / (σ√(2π))) * e^(-((x - μ)² / (2σ²)))
 *
 * Notes:
 *  - We skip code blocks.
 *  - We won’t wrap anything that already contains $…$ or $$…$$.
 */
function autoMathify(markdown: string): string {
  // split on fenced code blocks to avoid touching code
  const parts = markdown.split(/(```[\s\S]*?```)/g);
  return parts
    .map((chunk, i) => {
      // Leave fenced code blocks untouched (odd indices are the fences due to the split)
      if (i % 2 === 1) return chunk;

      // Work line-by-line for simple, safe replacements
      const lines = chunk.split('\n').map((line) => {
        const alreadyLaTeX = /\$(.|[\r\n])*\$/.test(line) || /\$\$/.test(line);
        if (alreadyLaTeX) return line;

        let out = line;

        // HTML <sup> → LaTeX superscripts
        out = out.replace(/<sup>(.*?)<\/sup>/gi, '^{$1}');

        // Common unicode superscripts (², ³)
        out = out.replace(/([A-Za-z0-9)\]}])²/g, '$1^{2}');
        out = out.replace(/([A-Za-z0-9)\]}])³/g, '$1^{3}');

        // sqrt: √( … ) -> \sqrt{ … }
        out = out.replace(/√\(([^)]+)\)/g, '\\sqrt{$1}');

        // Greek letters → LaTeX macros
        out = out.replace(/σ/g, '\\sigma');
        out = out.replace(/μ/g, '\\mu');
        out = out.replace(/π/g, '\\pi');

        // e^(...) and e^-x shapes → e^{...}
        out = out.replace(/e\^\(([^)]+)\)/g, 'e^{$1}');
        out = out.replace(/e\^(-?[A-Za-z0-9+/*\s._-]+)/g, (m, p1) => `e^{${p1.trim()}}`);

        // fraction: 1 / ( ... )  →  \frac{1}{ ... }
        out = out.replace(/(^|[^\\])1\s*\/\s*\(([^)]+)\)/g, (_m, pfx, inside) => `${pfx}\\frac{1}{${inside}}`);

        // If the line *looks* like a formula, wrap it in $…$
        const looksLikeFormula =
          /\\(sigma|mu|pi|sqrt|frac)|e\^{|=/.test(out) &&
          out.trim().length > 0;

        if (looksLikeFormula) {
          // Don't double-wrap if we already inserted $ earlier
          if (!/^\s*\$.*\$\s*$/.test(out)) out = `$${out}$`;
        }

        return out;
      });

      return lines.join('\n');
    })
    .join('');
}

/* ──────────────────────── UI primitives ─────────────────────── */

// const InlineCode = ({ children, ...props }: any) => (
//   <code
//     className="rounded px-1.5 py-0.5 font-mono text-[0.9em] bg-slate-200/70 text-slate-800"
//     {...props}
//   >
//     {children}
//   </code>
// );

/**
 * Dark themed <pre> wrapper that preserves Streamdown/Shiki HTML:
 *  • Language badge + line count
 *  • Copy button
 *  • Collapse/expand for long blocks with bottom fade
 */
// const PreBlock: React.FC<React.HTMLAttributes<HTMLPreElement>> = (props) => {
//   // Expect <pre><code class="language-xxx">…</code></pre>
//   const onlyChild = React.Children.only(props.children) as React.ReactElement<any>;
//   const className: string | undefined = onlyChild?.props?.className;
//   const language =
//     (className?.match(/language-([a-z0-9+#.-]+)/i)?.[1] ?? 'code').toLowerCase();

//   const raw = onlyChild?.props?.children;
//   const codeText = useMemo(() => extractText(raw).replace(/\n$/, ''), [raw]);
//   const lines = useMemo(() => codeText.split('\n'), [codeText]);
//   const blockId = useMemo(() => hashString(codeText), [codeText]);

//   const COLLAPSE_THRESHOLD = 14;
//   const [collapsed, setCollapsed] = useState(false);
//   const [copied, setCopied] = useState(false);

//   useEffect(() => {
//     setCollapsed(lines.length > COLLAPSE_THRESHOLD);
//     // eslint-disable-next-line react-hooks/exhaustive-deps
//   }, [blockId]);

//   const onCopy = async () => {
//     try {
//       await navigator.clipboard.writeText(codeText);
//       setCopied(true);
//       setTimeout(() => setCopied(false), 1100);
//     } catch {}
//   };

//   return (
//     <div className="my-4 overflow-hidden rounded-xl border border-slate-700/60 bg-[#0b1220] shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
//       {/* Header */}
//       <div className="flex items-center justify-between border-b border-slate-700/60 bg-[#0f172a] px-3 py-2.5">
//         <div className="flex items-center gap-3">
//           {lines.length > COLLAPSE_THRESHOLD && (
//             <button
//               onClick={() => setCollapsed((v) => !v)}
//               className="rounded p-1 text-slate-300/80 hover:bg-slate-800/50 hover:text-slate-100 transition"
//               title={collapsed ? 'Expand code' : 'Collapse code'}
//               aria-label={collapsed ? 'Expand code' : 'Collapse code'}
//             >
//               <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor">
//                 {collapsed ? (
//                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
//                 ) : (
//                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
//                 )}
//               </svg>
//             </button>
//           )}

//           <span className="rounded-md bg-slate-800/70 px-2 py-0.5 text-xs font-semibold capitalize text-slate-100">
//             {language}
//           </span>
//           <span className="text-xs text-slate-400">
//             {lines.length} line{lines.length !== 1 ? 's' : ''}
//           </span>
//         </div>

//         <button
//           onClick={onCopy}
//           className="rounded-md border border-slate-600 bg-slate-800/50 px-2 py-1 text-xs font-medium text-slate-100 hover:bg-slate-700/70 active:scale-[0.99] transition"
//           title="Copy code"
//         >
//           {copied ? 'Copied!' : 'Copy'}
//         </button>
//       </div>

//       {/* Body */}
//       <div className={`relative ${collapsed ? 'max-h-72 overflow-hidden' : ''}`}>
//         {/* IMPORTANT: don’t override the inner <code> — Streamdown/Shiki injects the colored spans there */}
//         <pre className="m-0 max-h-[70vh] overflow-x-auto p-4 text-[13px] leading-relaxed font-mono text-slate-200 bg-transparent">
//           {onlyChild}
//         </pre>

//         {collapsed && (
//           <>
//             <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-[#0b1220] to-transparent" />
//             <div className="flex justify-center pb-3">
//               <button
//                 onClick={() => setCollapsed(false)}
//                 className="relative z-10 -mt-6 rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-100 shadow-sm hover:bg-slate-700"
//               >
//                 Show more
//               </button>
//             </div>
//           </>
//         )}
//       </div>
//     </div>
//   );
// };

/* ───────────── component map (don’t override block <code>) ───────────── */

// export const createMarkdownComponents = () => ({
//   pre: PreBlock,

//   // Do NOT override block <code>; let Streamdown/Shiki render it.
//   // Style inline <code> with a small chip via CSS or the fragment below.
//   code: ({ inline, children, ...rest }: any) =>
//     inline ? (
//       <InlineCode {...rest}>{children}</InlineCode>
//     ) : (
//       // return default element; don’t touch Shiki output
//       <code {...rest}>{children}</code>
//     ),

//   /* Typography & elements */
//   p: ({ children, ...props }: any) => (
//     <p className="mb-3 last:mb-0 leading-relaxed text-slate-800" {...props}>
//       {children}
//     </p>
//   ),
//   ul: ({ children, ...props }: any) => (
//     <ul className="mb-3 ml-5 list-disc space-y-1 text-slate-800" {...props}>
//       {children}
//     </ul>
//   ),
//   ol: ({ children, ...props }: any) => (
//     <ol className="mb-3 ml-5 list-decimal space-y-1 text-slate-800" {...props}>
//       {children}
//     </ol>
//   ),
//   li: ({ children, ...props }: any) => (
//     <li className="leading-relaxed text-slate-800" {...props}>
//       {children}
//     </li>
//   ),
//   blockquote: ({ children, ...props }: any) => (
//     <blockquote
//       className="my-3 rounded-r border-l-4 border-slate-300 bg-slate-50/60 pl-4 italic text-slate-700"
//       {...props}
//     >
//       {children}
//     </blockquote>
//   ),
//   h1: ({ children, ...props }: any) => (
//     <h1 className="mb-3 border-b border-slate-200 pb-1 text-xl font-bold text-slate-900" {...props}>
//       {children}
//     </h1>
//   ),
//   h2: ({ children, ...props }: any) => (
//     <h2 className="mb-2 text-lg font-bold text-slate-900" {...props}>
//       {children}
//     </h2>
//   ),
//   h3: ({ children, ...props }: any) => (
//     <h3 className="mb-2 text-base font-semibold text-slate-900" {...props}>
//       {children}
//     </h3>
//   ),
//   h4: ({ children, ...props }: any) => (
//     <h4 className="mb-1 text-sm font-semibold text-slate-900" {...props}>
//       {children}
//     </h4>
//   ),
//   strong: ({ children, ...props }: any) => (
//     <strong className="font-semibold text-slate-900" {...props}>
//       {children}
//     </strong>
//   ),
//   em: ({ children, ...props }: any) => (
//     <em className="italic text-slate-800" {...props}>
//       {children}
//     </em>
//   ),
//   table: ({ children, ...props }: any) => (
//     <div className="my-3 overflow-x-auto">
//       <table className="min-w-full overflow-hidden rounded border border-slate-300 text-sm" {...props}>
//         {children}
//       </table>
//     </div>
//   ),
//   thead: ({ children, ...props }: any) => (
//     <thead className="bg-slate-100" {...props}>
//       {children}
//     </thead>
//   ),
//   tbody: ({ children, ...props }: any) => <tbody className="bg-white" {...props}>{children}</tbody>,
//   tr: ({ children, ...props }: any) => (
//     <tr className="border-b border-slate-200" {...props}>
//       {children}
//     </tr>
//   ),
//   th: ({ children, ...props }: any) => (
//     <th className="border-r border-slate-200 px-3 py-2 text-left font-semibold text-slate-900 last:border-r-0" {...props}>
//       {children}
//     </th>
//   ),
//   td: ({ children, ...props }: any) => (
//     <td className="border-r border-slate-200 px-3 py-2 text-slate-800 last:border-r-0" {...props}>
//       {children}
//     </td>
//   ),
//   a: ({ href, children, ...props }: any) => (
//     <a
//       href={href}
//       target="_blank"
//       rel="noopener noreferrer"
//       className="underline decoration-slate-400 underline-offset-2 text-blue-700 hover:text-blue-900"
//       {...props}
//     >
//       {children}
//     </a>
//   ),
//   img: ({ src, alt }: any) => {
//     const mdSrc = typeof src === 'string' ? src.trim() : '';
//     if (!mdSrc) return null;
//     return (
//       <div className="my-4 text-center">
//         <ImageWithHistory src={mdSrc} alt={alt} maxHeight="500px" />
//         {alt && <p className="mt-2 text-sm italic text-slate-500">{alt}</p>}
//       </div>
//     );
//   },
// });








interface ChatMessagesProps {
  activeConversation: Conversation;
  isLoading: boolean;
  collapsedBlocks: Set<string>; // kept for prop compatibility (unused)
  copiedCode: string;           // kept for prop compatibility (unused)
  onNavigateUserEdit: (messageId: string, direction: 'prev' | 'next') => void;
  onNavigateResponse: (messageId: string, direction: 'prev' | 'next') => void;
  onRegenerateResponse: (messageId: string) => void;
  onToggleCodeBlock: (blockId: string) => void;                // kept for prop compatibility (unused)
  onCopyCode: (text: string, blockId: string) => void;         // kept for prop compatibility (unused)
  onToggleEdit: (messageId: string) => void;
  onRegenerateFromMessage: (messageId: string, newText: string, files: FileData[]) => void;
  messagesEndRef: RefObject<HTMLDivElement>;
}

// Editable message component
const EditableMessage = ({
  msg,
  onSave,
  onCancel
}: {
  msg: Message;
  onSave: (text: string) => void;
  onCancel: () => void;
}) => {
  const [editText, setEditText] = React.useState(msg.text);

  const handleSave = () => {
    if (editText.trim()) {
      onSave(editText.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      onCancel();
    }
  };

  return (
    <div className="space-y-3">
      {/* Edit Form */}
      <div className="card-bg backdrop-blur-sm rounded-lg p-4 border card-border shadow-sm">
        <textarea
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full p-3 border input-border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 input-text input-bg shadow-sm transition-all duration-200"
          rows={Math.max(2, editText.split('\n').length)}
          autoFocus
          placeholder="Type your message..."
        />
      </div>

      {/* Action Bar */}
      <div className="flex justify-center">
        <div className="flex items-center gap-1 action-button-group">
          <button
            onClick={onCancel}
            className="p-1.5 nav-button rounded-md group"
            title="Cancel editing"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="w-px h-4 nav-border mx-1"></div>

          <button
            onClick={handleSave}
            className="p-1.5 nav-button rounded-md group disabled:opacity-40 disabled:hover:bg-transparent"
            disabled={!editText.trim()}
            title="Save & regenerate"
          >
            <Check className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

// File preview in message
const MessageFilePreview = ({ file, index }: { file: FileData; index: number }) => {
  const isImage = file.mime_type.startsWith('image/');

  if (isImage) {
    return (
      <div key={index} className="relative inline-block m-1 group">
        <img
          src={file.url || `data:${file.mime_type};base64,${file.data}`}
          alt={file.filename}
          className="max-w-full sm:max-w-xs max-h-48 sm:max-h-64 rounded-xl object-cover border border-gray-200 shadow-sm cursor-pointer hover:shadow-lg transition-all duration-200"
          onClick={() => window.open(file.url || `data:${file.mime_type};base64,${file.data}`, '_blank')}
        />
      </div>
    );
  } else {
    return (
      <div
        key={index}
        className="inline-flex items-center gap-1 sm:gap-2 m-1 px-2 sm:px-3 py-1.5 sm:py-2 file-preview-item rounded-xl text-xs sm:text-sm"
      >
        <div className="flex items-center gap-1 sm:gap-2 file-preview-text">
          <FileIcon mimeType={file.mime_type} className="w-3 h-3 sm:w-4 sm:h-4 file-preview-icon" />
          <span className="truncate max-w-20 sm:max-w-32 font-medium">{file.filename}</span>
        </div>
      </div>
    );
  }
};

// Typing indicator
const TypingIndicator = () => {
  return (
            <div className="flex items-center space-x-2 py-3">
      <div className="flex space-x-1">
        <div className="w-2 h-2 typing-dot-bg rounded-full typing-dot"></div>
        <div className="w-2 h-2 typing-dot-bg rounded-full typing-dot"></div>
        <div className="w-2 h-2 typing-dot-bg rounded-full typing-dot"></div>
      </div>
      <span className="typing-text text-sm">AI is thinking...</span>
    </div>
  );
};

// Streaming text wrapper
const StreamingText = ({ text, isComplete }: { text: string; isComplete: boolean }) => {
  const content = useMemo(() => autoMathify(text), [text]);
  return (
    <div className="min-w-0 overflow-hidden">
      <Streamdown
        parseIncompleteMarkdown={true}
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        // Ensure Shiki uses a dark theme so tokens pop on our dark pre background
        shikiTheme={["github-dark", "github-dark"]}
        components={{ code: LLMCodeBlock as any }}
      >
        {normalizeFences(content)}
      </Streamdown>
    </div>
  );
};

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  activeConversation,
  isLoading,
  collapsedBlocks, // unused
  copiedCode,      // unused
  onNavigateUserEdit,
  onNavigateResponse,
  onRegenerateResponse,
  onToggleCodeBlock, // unused
  onCopyCode,        // unused
  onToggleEdit,
  onRegenerateFromMessage,
  messagesEndRef
}) => {
  return (
    <div className="flex-1 overflow-y-auto bg-transparent custom-scrollbar h-full mobile-scroll">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 min-h-full">
        {activeConversation.messages.length === 0 && !isLoading && (
          <div className="text-center py-12 sm:py-16 md:py-20">
            <div className="relative mb-6 sm:mb-8 mx-auto w-24 h-24 sm:w-28 sm:h-28 md:w-32 md:h-32">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-indigo-600 rounded-3xl shadow-2xl transform rotate-3 animate-pulse"></div>
              <div className="relative w-full h-full bg-white dark:bg-gunmetal-2 rounded-3xl shadow-xl flex items-center justify-center transform -rotate-3 hover:rotate-0 transition-transform duration-500">
                <MessageCircle className="w-10 h-10 sm:w-12 sm:h-12 md:w-16 md:h-16 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
            <h4 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-gray-800 via-blue-800 to-purple-800 dark:from-blue-200 dark:via-purple-200 dark:to-indigo-200 bg-clip-text text-transparent mb-4">
              Welcome to Xbot!
            </h4>
            <p className="text-gray-600 dark:text-gray-300 mb-6 sm:mb-8 text-base sm:text-lg leading-relaxed max-w-2xl mx-auto px-4">
              Your intelligent AI assistant powered by multiple advanced language models.
              <br />
              Ready to help with questions, analysis, creativity, and more.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 max-w-4xl mx-auto mb-6 sm:mb-8 px-4 welcome-cards-container">
              <div className="group p-4 sm:p-5 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-gunmetal-2 dark:to-charcoal-2 rounded-2xl border border-blue-200 dark:border-charcoal/30 hover:shadow-lg dark:hover:shadow-blue-500/10 transition-all duration-300 hover:-translate-y-1">
                <div className="w-8 h-8 sm:w-10 sm:h-10 bg-blue-500 dark:bg-blue-600 rounded-xl flex items-center justify-center mb-2 sm:mb-3 mx-auto group-hover:scale-110 transition-transform">
                  <MessageCircle className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                </div>
                <span className="text-blue-800 dark:text-blue-200 text-sm sm:text-base font-semibold">Chat</span>
              </div>
              <div className="group p-4 sm:p-5 bg-gradient-to-br from-green-50 to-green-100 dark:from-gunmetal-2 dark:to-charcoal-2 rounded-2xl border border-green-200 dark:border-charcoal/30 hover:shadow-lg dark:hover:shadow-green-500/10 transition-all duration-300 hover:-translate-y-1">
                <div className="w-8 h-8 sm:w-10 sm:h-10 bg-green-500 dark:bg-green-600 rounded-xl flex items-center justify-center mb-2 sm:mb-3 mx-auto group-hover:scale-110 transition-transform">
                  <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                </div>
                <span className="text-green-800 dark:text-green-200 text-sm sm:text-base font-semibold">Documents</span>
              </div>
              <div className="group p-4 sm:p-5 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-gunmetal-2 dark:to-charcoal-2 rounded-2xl border border-purple-200 dark:border-charcoal/30 hover:shadow-lg dark:hover:shadow-purple-500/10 transition-all duration-300 hover:-translate-y-1">
                <div className="w-8 h-8 sm:w-10 sm:h-10 bg-purple-500 dark:bg-purple-600 rounded-xl flex items-center justify-center mb-2 sm:mb-3 mx-auto group-hover:scale-110 transition-transform">
                  <ImageIcon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                </div>
                <span className="text-purple-800 dark:text-purple-200 text-sm sm:text-base font-semibold">Images</span>
              </div>
              <div className="group p-4 sm:p-5 bg-gradient-to-br from-orange-50 to-orange-100 dark:from-gunmetal-2 dark:to-charcoal-2 rounded-2xl border border-orange-200 dark:border-charcoal/30 hover:shadow-lg dark:hover:shadow-orange-500/10 transition-all duration-300 hover:-translate-y-1">
                <div className="w-8 h-8 sm:w-10 sm:h-10 bg-orange-500 dark:bg-orange-600 rounded-xl flex items-center justify-center mb-2 sm:mb-3 mx-auto group-hover:scale-110 transition-transform">
                  <Bot className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                </div>
                <span className="text-orange-800 dark:text-orange-200 text-sm sm:text-base font-semibold">Analysis</span>
              </div>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">💡 Try asking questions, uploading files, or generating images</p>
          </div>
        )}

        {activeConversation.messages.map((msg, idx) => (
          <div key={msg.id || idx} className={`mb-6 sm:mb-8 ${msg.sender === 'User' ? 'group' : ''}`}>
            <div className={`flex ${msg.sender === 'User' ? 'justify-end' : 'justify-start'}`}>
                              <div
                                  className={`flex gap-3 sm:gap-4 lg:gap-5 ${
                  msg.sender === 'User' ? 'max-w-[90%] sm:max-w-[85%] md:max-w-[80%] lg:max-w-[75%] xl:max-w-[70%]' : 'max-w-[95%] sm:max-w-[92%] md:max-w-[90%] lg:max-w-[88%] xl:max-w-[85%]'
                } ${msg.sender === 'User' ? 'flex-row-reverse' : 'flex-row'}`}
                >
                {/* Avatar */}
                <div
                  className={`
                w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 rounded-2xl flex items-center justify-center flex-shrink-0 mt-1 shadow-lg ring-2 ring-white
                ${msg.sender === 'User'
                    ? 'avatar-user'
                    : 'avatar-bot'
                  }
              `}
                >
                  {msg.sender === 'User' ? (
                    <User className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                  )}
                </div>

                {/* Message Content */}
                <div
                  className={`
                px-4 sm:px-5 md:px-6 py-4 sm:py-5 rounded-2xl shadow-lg border backdrop-blur-sm relative group transition-all duration-200 hover:shadow-xl min-w-0 flex-1
                ${msg.sender === 'User'
                    ? 'chat-message-user'
                    : 'chat-message-bot'
                  }
                ${msg.sender === 'User' ? 'rounded-tr-lg' : 'rounded-tl-lg'}
              `}
                >
                  {/* Bot Action buttons - only for bot messages */}
                  {msg.sender === 'Bot' && (
                    <div className="absolute top-1 sm:top-2 right-1 sm:right-2 flex items-center space-x-1 sm:space-x-2 opacity-0 group-hover:opacity-100 transition-all duration-300">
                      {/* Bot message navigation and regenerate buttons */}
                      {!msg.isStreaming && !isLoading && (
                        <>
                          {msg.responses && msg.responses.length > 1 && (
                            <div className="flex items-center gap-1 action-button-group">
                              <button
                                onClick={() => onNavigateResponse(msg.id, 'prev')}
                                disabled={(msg.currentResponseIndex || 0) === 0}
                                className="p-0.5 sm:p-1 nav-button rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                title="Previous response"
                              >
                                <ChevronLeft className="w-3 h-3 sm:w-4 sm:h-4" />
                              </button>

                              <span className="text-xs nav-text px-1 sm:px-2 font-medium">
                                {(msg.currentResponseIndex || 0) + 1} / {msg.responses.length}
                              </span>

                              <button
                                onClick={() => onNavigateResponse(msg.id, 'next')}
                                disabled={(msg.currentResponseIndex || 0) === (msg.responses?.length || 1) - 1}
                                className="p-0.5 sm:p-1 nav-button rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                title="Next response"
                              >
                                <ChevronRight className="w-3 h-3 sm:w-4 sm:h-4" />
                              </button>
                            </div>
                          )}

                          <button
                            onClick={() => onRegenerateResponse(msg.id)}
                            className="p-1 sm:p-1.5 action-button"
                            title="Regenerate response"
                          >
                            <RotateCcw className="w-3 h-3 sm:w-4 sm:h-4" />
                          </button>
                        </>
                      )}
                    </div>
                  )}

                  {/* Message content rendering */}
                  {msg.isEditing ? (
                    <EditableMessage
                      msg={msg}
                      onSave={(newText) => {
                        onRegenerateFromMessage(msg.id, newText, msg.files || []);
                      }}
                      onCancel={() => onToggleEdit(msg.id)}
                    />
                  ) : (
                    <>
                      {/* typing indicator for just-started streams */}
                      {msg.sender === 'Bot' && msg.isStreaming && !msg.text && <TypingIndicator />}

                      {/* Message Text */}
                      {msg.text && (
                        <div className="mb-3 last:mb-0 min-w-0">
                          {msg.sender === 'User' ? (
                            <div className="whitespace-pre-wrap break-words leading-relaxed text-sm sm:text-[15px] overflow-hidden">{msg.text}</div>
                          ) : msg.isStreaming ? (
                            <div className="min-w-0 overflow-hidden">
                              <StreamingText text={msg.text} isComplete={false} />
                            </div>
                          ) : (
                            <div className="min-w-0 overflow-hidden">
                              <StreamingText text={msg.text} isComplete={true} />
                            </div>
                          )}
                        </div>
                      )}

                      {/* Files */}
                      {msg.files && msg.files.length > 0 && (
                        <div className="mt-4">
                          {msg.files.map((file, fileIndex) => (
                            <MessageFilePreview key={fileIndex} file={file} index={fileIndex} />
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* User Message Actions Bar */}
            {msg.sender === 'User' && !msg.isEditing && (
              <div className="flex justify-end mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <div className="flex items-center gap-0.5 action-button-group">
                  {/* Copy Message Button */}
                  <button
                    onClick={() => navigator.clipboard.writeText(msg.text)}
                    className="p-1 nav-button rounded group"
                    title="Copy message"
                  >
                    <svg
                      className="w-3.5 h-3.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                      />
                    </svg>
                  </button>

                  {/* Edit Message Button */}
                  {!isLoading && (
                    <button
                      onClick={() => onToggleEdit(msg.id)}
                      className="p-1 nav-button rounded group"
                      title="Edit message"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                  )}

                  {/* Navigation for multiple versions */}
                  {((msg.edits && msg.edits.length > 1) || (msg.branches && msg.branches.length > 1)) && !isLoading && (
                    <>
                      <div className="w-px h-3 nav-border mx-0.5"></div>
                      <button
                        onClick={() => onNavigateUserEdit(msg.id, 'prev')}
                        disabled={
                          msg.edits && msg.edits.length > 1
                            ? (msg.currentEditIndex ?? msg.edits.length - 1) === 0
                            : (msg.currentBranchIndex ?? 0) === 0
                        }
                        className="p-1 nav-button rounded group disabled:opacity-40 disabled:hover:bg-transparent"
                        title="Previous version"
                      >
                        <ChevronLeft className="w-3.5 h-3.5" />
                      </button>

                      <span className="px-1.5 py-0.5 text-xs font-medium nav-text">
                        {msg.edits && msg.edits.length > 1
                          ? `${(msg.currentEditIndex ?? msg.edits.length - 1) + 1}/${msg.edits.length}`
                          : `${(msg.currentBranchIndex ?? 0) + 1}/${msg.branches?.length || 1}`}
                      </span>

                      <button
                        onClick={() => onNavigateUserEdit(msg.id, 'next')}
                        disabled={
                          msg.edits && msg.edits.length > 1
                            ? (msg.currentEditIndex ?? msg.edits.length - 1) === msg.edits.length - 1
                            : (msg.currentBranchIndex ?? 0) === (msg.branches?.length || 1) - 1
                        }
                        className="p-1 nav-button rounded group disabled:opacity-40 disabled:hover:bg-transparent"
                        title="Next version"
                      >
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};


