// // MarkdownRenderer.tsx
// import React, { useEffect, useMemo, useState } from 'react';
// import { Streamdown } from 'streamdown';
// import remarkGfm from 'remark-gfm';
// import remarkMath from 'remark-math';
// import rehypeKatex from 'rehype-katex';
// import 'katex/dist/katex.min.css';

// // If you use images in markdown, keep your original helper. Adjust the path if needed.
// import { ImageWithHistory } from '../../Component/ImageWithHistory';

// /* ───────────────────────── helpers ───────────────────────── */

// // stable (deterministic) id for a code block based on its contents
// function hashString(input: string) {
//   let h = 0;
//   for (let i = 0; i < input.length; i++) {
//     h = (h << 5) - h + input.charCodeAt(i);
//     h |= 0;
//   }
//   return `code-${Math.abs(h)}`;
// }

// // Extract plain text out of any React children tree
// function extractText(node: any): string {
//   if (node == null) return '';
//   if (typeof node === 'string') return node;
//   if (Array.isArray(node)) return node.map(extractText).join('');
//   if (React.isValidElement(node)) return extractText((node as any).props?.children);
//   return '';
// }

// /**
//  * Auto-convert common “plain text” math to LaTeX so KaTeX renders it nicely.
//  * This is intentionally conservative and targets the exact shapes from your screenshots:
//  *  - σ(x) = 1 / (1 + e<sup>-x</sup>)
//  *  - f(x) = (1 / (σ√(2π))) * e^(-((x - μ)² / (2σ²)))
//  *
//  * Notes:
//  *  - We skip code blocks.
//  *  - We won’t wrap anything that already contains $…$ or $$…$$.
//  */
// function autoMathify(markdown: string): string {
//   // split on fenced code blocks to avoid touching code
//   const parts = markdown.split(/(```[\s\S]*?```)/g);
//   return parts
//     .map((chunk, i) => {
//       // Leave fenced code blocks untouched (odd indices are the fences due to the split)
//       if (i % 2 === 1) return chunk;

//       // Work line-by-line for simple, safe replacements
//       const lines = chunk.split('\n').map((line) => {
//         const alreadyLaTeX = /\$(.|[\r\n])*\$/.test(line) || /\$\$/.test(line);
//         if (alreadyLaTeX) return line;

//         let out = line;

//         // HTML <sup> → LaTeX superscripts
//         out = out.replace(/<sup>(.*?)<\/sup>/gi, '^{$1}');

//         // Common unicode superscripts (², ³)
//         out = out.replace(/([A-Za-z0-9)\]}])²/g, '$1^{2}');
//         out = out.replace(/([A-Za-z0-9)\]}])³/g, '$1^{3}');

//         // sqrt: √( … ) -> \sqrt{ … }
//         out = out.replace(/√\(([^)]+)\)/g, '\\\\sqrt{$1}');

//         // Greek letters → LaTeX macros
//         out = out.replace(/σ/g, '\\\\sigma');
//         out = out.replace(/μ/g, '\\\\mu');
//         out = out.replace(/π/g, '\\\\pi');

//         // e^(...) and e^-x shapes → e^{...}
//         out = out.replace(/e\^\(([^)]+)\)/g, 'e^{${1}}');
//         out = out.replace(/e\^(-?[A-Za-z0-9+/*\s._-]+)/g, (m, p1) => `e^{${p1.trim()}}`);

//         // fraction: 1 / ( ... )  →  \frac{1}{ ... }
//         out = out.replace(/(^|[^\\])1\s*\/\s*\(([^)]+)\)/g, (_m, pfx, inside) => `${pfx}\\frac{1}{${inside}}`);

//         // If the line *looks* like a formula, wrap it in $…$
//         const looksLikeFormula =
//           /\\(sigma|mu|pi|sqrt|frac)|e\^{|=/.test(out) &&
//           out.trim().length > 0;

//         if (looksLikeFormula) {
//           // Don’t double-wrap if we already inserted $ earlier
//           if (!/^\s*\$.*\$\s*$/.test(out)) out = `$${out}$`;
//         }

//         return out;
//       });

//       return lines.join('\n');
//     })
//     .join('');
// }

// /* ──────────────────────── UI primitives ─────────────────────── */

// const InlineCode = ({ children, ...props }: any) => (
//   <code
//     className="rounded px-1.5 py-0.5 font-mono text-[0.9em] bg-slate-200/70 text-slate-800"
//     {...props}
//   >
//     {children}
//   </code>
// );

// /**
//  * Dark themed <pre> wrapper that preserves Streamdown/Shiki HTML:
//  *  • Language badge + line count
//  *  • Copy button
//  *  • Collapse/expand for long blocks with bottom fade
//  */
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

// /* ───────────── component map (don’t override block <code>) ───────────── */

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

// /* ───────────────────────── main renderer ───────────────────────── */

// interface MarkdownRendererProps {
//   children: string;
//   isStreaming?: boolean;
// }

// export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
//   children,
//   isStreaming = false,
// }) => {
//   // Pre-process to auto-LaTeX common formulas
//   const content = useMemo(() => autoMathify(children), [children]);

//   // Access extra props that might not be typed in older versions
//   const StreamdownAny = Streamdown as any;

//   return (
//     <div className="prose prose-sm max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
//       <Streamdown
//         // GFM + Math → KaTeX
//         parseIncompleteMarkdown={true}
//         remarkPlugins={[remarkGfm, remarkMath]}
//         rehypePlugins={[rehypeKatex]}
//         // Ensure Shiki uses a dark theme so tokens pop on our dark pre background
//         // shikiTheme={["github-dark"]}
//         components={createMarkdownComponents()}
//       >
//         {content}
//       </Streamdown>

//       {isStreaming && (
//         <span className="ml-1 inline-block h-5 w-2 animate-pulse rounded-sm bg-blue-500" />
//       )}
//     </div>
//   );
// };
