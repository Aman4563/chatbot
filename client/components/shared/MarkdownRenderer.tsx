import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { visit } from 'unist-util-visit';
import { ImageWithHistory } from '../../Component/ImageWithHistory';

// Rehype plugin to strip hljs classes
function rehypeStripHljs() {
  return (tree: any) => {
    visit(tree, 'element', (node: any) => {
      if (
        node.tagName === 'code' &&
        Array.isArray(node.properties?.className)
      ) {
        node.properties.className = node.properties.className.filter(
          (c: string) => c !== 'hljs'
        );
      }
    });
  };
}

// Inline code component
const InlineCode = ({ children, ...props }: any) => (
  <code
    className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono"
    {...props}
  >
    {children}
  </code>
);

// Common markdown components
export const createMarkdownComponents = (
  codeBlockComponent?: React.ComponentType<any>
) => ({
  code: ({ inline, className, children, ...props }: any) => {
    const text = String(children).replace(/\n$/, '');
    const hasLang = Boolean(className);
    const isSingleLine = !text.includes('\n');

    if (inline) {
      return <InlineCode {...props}>{children}</InlineCode>;
    }

    if (isSingleLine && !hasLang) {
      return <InlineCode {...props}>{children}</InlineCode>;
    }

    // Use custom code block component if provided, otherwise use simple version
    if (codeBlockComponent) {
      const CodeBlockComponent = codeBlockComponent;
      return (
        <CodeBlockComponent className={className} {...props}>
          {children}
        </CodeBlockComponent>
      );
    }

    // Simple code block for streaming
    return (
      <div className="my-4 rounded-lg overflow-hidden border border-gray-200 shadow-sm bg-white">
        <div className="bg-gray-50 px-4 py-2.5 flex items-center justify-between border-b border-gray-200">
          <span className="text-gray-600 text-sm font-medium capitalize">
            {className?.replace(/language-/, '') || 'Code'}
          </span>
        </div>
        <div className="relative">
          <pre className="bg-gray-900 text-gray-100 p-4 overflow-x-auto text-sm font-mono leading-relaxed custom-scrollbar">
            <code className={className}>
              {children}
            </code>
          </pre>
        </div>
      </div>
    );
  },
  pre: ({ children }: any) => <>{children}</>,
  p: ({ children, ...props }: any) => (
    <p className="mb-3 last:mb-0 leading-relaxed text-gray-700" {...props}>
      {children}
    </p>
  ),
  ul: ({ children, ...props }: any) => (
    <ul className="list-disc ml-5 mb-3 space-y-1" {...props}>
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: any) => (
    <ol className="list-decimal ml-5 mb-3 space-y-1" {...props}>
      {children}
    </ol>
  ),
  li: ({ children, ...props }: any) => (
    <li className="text-gray-700 leading-relaxed" {...props}>
      {children}
    </li>
  ),
  blockquote: ({ children, ...props }: any) => (
    <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-3 bg-gray-50 py-2 rounded-r" {...props}>
      {children}
    </blockquote>
  ),
  h1: ({ children, ...props }: any) => (
    <h1 className="text-xl font-bold mb-3 text-gray-800 border-b border-gray-200 pb-1" {...props}>
      {children}
    </h1>
  ),
  h2: ({ children, ...props }: any) => (
    <h2 className="text-lg font-bold mb-2 text-gray-800" {...props}>
      {children}
    </h2>
  ),
  h3: ({ children, ...props }: any) => (
    <h3 className="text-base font-semibold mb-2 text-gray-800" {...props}>
      {children}
    </h3>
  ),
  h4: ({ children, ...props }: any) => (
    <h4 className="text-sm font-semibold mb-1 text-gray-800" {...props}>
      {children}
    </h4>
  ),
  strong: ({ children, ...props }: any) => (
    <strong className="font-semibold text-gray-800" {...props}>
      {children}
    </strong>
  ),
  em: ({ children, ...props }: any) => (
    <em className="italic text-gray-700" {...props}>
      {children}
    </em>
  ),
  table: ({ children, ...props }: any) => (
    <div className="overflow-x-auto my-3">
      <table className="min-w-full border border-gray-300 rounded overflow-hidden text-sm" {...props}>
        {children}
      </table>
    </div>
  ),
  thead: ({ children, ...props }: any) => (
    <thead className="bg-gray-100" {...props}>
      {children}
    </thead>
  ),
  tbody: ({ children, ...props }: any) => (
    <tbody className="bg-white" {...props}>
      {children}
    </tbody>
  ),
  tr: ({ children, ...props }: any) => (
    <tr className="border-b border-gray-200" {...props}>
      {children}
    </tr>
  ),
  th: ({ children, ...props }: any) => (
    <th className="px-3 py-2 text-left font-semibold text-gray-800 border-r border-gray-200 last:border-r-0" {...props}>
      {children}
    </th>
  ),
  td: ({ children, ...props }: any) => (
    <td className="px-3 py-2 text-gray-700 border-r border-gray-200 last:border-r-0" {...props}>
      {children}
    </td>
  ),
  a: ({ href, children, ...props }: any) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 underline" {...props}>
      {children}
    </a>
  ),
  img: ({ src, alt }: any) => {
    const mdSrc = typeof src === 'string' ? src.trim() : '';

    if (!mdSrc) return null;

    return (
      <div className="my-4 text-center">
        <ImageWithHistory src={mdSrc} alt={alt} maxHeight="500px" />
        {alt && <p className="mt-2 text-sm italic text-gray-500">{alt}</p>}
      </div>
    );
  },
});

interface MarkdownRendererProps {
  children: string;
  codeBlockComponent?: React.ComponentType<any>;
  isStreaming?: boolean;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  children,
  codeBlockComponent,
  isStreaming = false
}) => {
  return (
    <div className="prose prose-sm max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeStripHljs]}
        components={createMarkdownComponents(codeBlockComponent)}
      >
        {children}
      </ReactMarkdown>
      {isStreaming && (
        <span className="inline-block w-2 h-5 bg-blue-500 ml-1 streaming-cursor rounded-sm"></span>
      )}
    </div>
  );
};
