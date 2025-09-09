"use client";

import React, { useEffect, useMemo, useState, useId } from "react";
import mermaid from "mermaid";
import { codeToHtml } from "shiki";
import {
  transformerNotationDiff,
  transformerNotationHighlight,
  transformerNotationFocus,
  transformerMetaHighlight,
  transformerMetaWordHighlight,
} from "@shikijs/transformers";
import { useSelector } from "react-redux";
import { RootState } from "../../store";

// Parse "meta" like: ```
function parseInfo(className?: string, meta?: string) {
  const lang = (className || "").replace("language-", "") || "txt";
  const titleMatch = meta?.match(/(?:title|file|filename)=(?:"([^"]+)"|([^\s]+))/i);
  const title = titleMatch?.[1] || titleMatch?.[2] || lang;
  return { lang, title, meta };
}

type CodeProps = {
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
  node?: any;
  [key: string]: any;
};

function escapeHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/** Lightweight Mermaid renderer for ```mermaid``` fences */
function MermaidBlock({
  code,
  theme,
}: {
  code: string;
  theme: "default" | "dark" | "forest" | "neutral";
}) {
  const id = useId();
  const [svg, setSvg] = useState<string>("");
  const [err, setErr] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    // Initialize Mermaid for this render pass
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme,
    });

    (async () => {
      try {
        const { svg } = await mermaid.render(id, code);
        if (!cancelled) {
          setSvg(svg);
          setErr(null);
          setIsLoading(false);
        }
      } catch (e: any) {
        if (!cancelled) {
          setErr(e?.message || "Failed to render diagram");
          setSvg("");
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [code, id, theme]);

  if (isLoading) {
    return (
      <div className="p-4 text-xs text-slate-500 dark:text-slate-400">
        Rendering diagram…
      </div>
    );
  }

  if (err) {
    return (
      <div className="p-4">
        <div className="flex items-start gap-3 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
          <div className="flex-shrink-0 mt-0.5">
            <svg className="w-4 h-4 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-orange-700 dark:text-orange-300 mb-2">
              Unable to render diagram due to syntax error.
            </p>
            <details className="group">
              <summary className="cursor-pointer text-xs text-orange-600 dark:text-orange-400 hover:text-orange-700 dark:hover:text-orange-300 font-medium">
                View diagram code
              </summary>
              <pre className="mt-2 overflow-auto rounded bg-orange-100 dark:bg-orange-900/30 p-3 text-xs text-orange-800 dark:text-orange-200 border border-orange-200 dark:border-orange-800">
                {code}
              </pre>
            </details>
          </div>
        </div>
      </div>
    );
  }

  return <div className="p-4" dangerouslySetInnerHTML={{ __html: svg }} />;
}

export function LLMCodeBlock({ inline, className, children, node, ...rest }: CodeProps) {
  // Get settings from Redux
  const { codeBlockTheme, showLineNumbers, showLanguageBadge, autoWrapCode, websiteTheme } = useSelector(
    (state: RootState) => state.settings
  );

  // ALL HOOKS MUST BE CALLED BEFORE ANY CONDITIONAL RETURNS
  const raw = useMemo(() => String(children ?? ""), [children]);
  const meta = (rest as any)?.["data-meta"] ?? node?.meta ?? "";
  const { lang, title } = useMemo(() => parseInfo(className, meta), [className, meta]);

  // Map common aliases -> Shiki/standard names (keep 'mermaid' as-is)
  const languageMap: Record<string, string> = {
    py: "python",
    js: "javascript",
    ts: "typescript",
    jsx: "jsx",
    tsx: "tsx",
    html: "html",
    css: "css",
    json: "json",
    yaml: "yaml",
    yml: "yaml",
    md: "markdown",
    sh: "bash",
    bash: "bash",
    zsh: "bash",
    ps1: "powershell",
    sql: "sql",
    java: "java",
    cpp: "cpp",
    c: "c",
    cs: "csharp",
    php: "php",
    rb: "ruby",
    go: "go",
    rs: "rust",
    swift: "swift",
    kt: "kotlin",
    scala: "scala",
    r: "r",
    matlab: "matlab",
    tex: "latex",
    latex: "latex",
    mermaid: "mermaid",
  };

  const mappedLang = languageMap[lang] || lang;

  const [html, setHtml] = useState<string>("");
  const [wrap, setWrap] = useState<boolean>(autoWrapCode);
  const [themeKey, setThemeKey] = useState<string>("");

  // Update wrap state when autoWrapCode setting changes
  useEffect(() => {
    setWrap(autoWrapCode);
  }, [autoWrapCode]);

  // Determine the actual theme to use for code highlighting
  const getEffectiveTheme = () => {
    let theme = "github-light"; // default

    if (websiteTheme === "dark") {
      theme = "github-dark";
    } else if (websiteTheme === "light") {
      theme = "github-light";
    } else if (websiteTheme === "auto") {
      if (typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        theme = "github-dark";
      } else {
        theme = "github-light";
      }
    }

    return theme;
  };

  // Mermaid theme from site theme
  const getMermaidTheme = (): "default" | "dark" | "forest" | "neutral" => {
    const eff = getEffectiveTheme();
    return /dark/i.test(eff) ? "dark" : "default";
  };

  // Update theme key when website theme changes to force re-render
  useEffect(() => {
    const effectiveTheme = getEffectiveTheme();
    setThemeKey(effectiveTheme);
  }, [websiteTheme]);

  // Only run Shiki for non-Mermaid blocks
  useEffect(() => {
    if (mappedLang === "mermaid") {
      setHtml(""); // ensure Shiki HTML isn't shown for Mermaid
      return;
    }

    let cancelled = false;
    const effectiveTheme = getEffectiveTheme();

    codeToHtml(raw, {
      lang: mappedLang,
      theme: effectiveTheme,
      transformers: [
        transformerNotationDiff(),
        transformerNotationHighlight(),
        transformerNotationFocus(),
        transformerMetaHighlight(),
        transformerMetaWordHighlight(),
      ],
      meta,
    })
      .then((out) => {
        if (!cancelled) {
          setHtml(out);
        }
      })
      .catch(() => {
        if (!cancelled) setHtml(`<pre><code>${escapeHtml(raw)}</code></pre>`);
      });
    return () => {
      cancelled = true;
    };
  }, [raw, mappedLang, meta, themeKey]);

  // UX: line count for the header badge
  const lineCount = useMemo(() => raw.split("\n").length, [raw]);

  // Mermaid-specific memoized values (always computed, but only used for mermaid)
  const mermaidTheme = useMemo(() => getMermaidTheme(), [websiteTheme]);
  const cleanedMermaid = useMemo(() => raw, [raw]);

  // Inline: never run Shiki to avoid conflicts with single backticks
  if (inline || !/language-/.test(className || "")) {
    return (
      <code className="rounded px-1.5 py-0.5 font-mono text-[0.9em] code-inline">
        {children}
      </code>
    );
  }

  // --- MERMAID RENDER PATH ---------------------------------------------------
  if (mappedLang === "mermaid") {
    return (
      <div className="my-4 overflow-hidden rounded-xl border code-block-border code-block-bg shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b code-header-border code-header-bg px-3 py-2.5">
          <div className="flex items-center gap-3">
            {showLanguageBadge && (
              <span className="rounded-md code-lang-bg px-2 py-0.5 text-xs font-semibold capitalize code-lang-text">
                {title || "mermaid"}
              </span>
            )}
            <span className="text-xs code-header-text">
              {lineCount} line{lineCount !== 1 ? "s" : ""}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label="Copy diagram source"
              className="rounded-md border code-button-border code-button-bg px-2 py-1 text-xs font-medium code-button-text hover:bg-slate-50 dark:hover:bg-slate-600 active:scale-[0.99] transition"
              onClick={() => navigator.clipboard.writeText(cleanedMermaid)}
            >
              Copy source
            </button>
          </div>
        </div>

        {/* Body (Mermaid SVG) */}
        <div className="relative">
          <MermaidBlock code={cleanedMermaid} theme={mermaidTheme} />
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------

  // DEFAULT (non-Mermaid) RENDER PATH WITH SHIKI
  return (
    <div className="my-4 overflow-hidden rounded-xl border code-block-border code-block-bg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between border-b code-header-border code-header-bg px-3 py-2.5">
        <div className="flex items-center gap-3">
          {showLanguageBadge && (
            <span className="rounded-md code-lang-bg px-2 py-0.5 text-xs font-semibold capitalize code-lang-text">
              {title}
            </span>
          )}
          <span className="text-xs code-header-text">
            {lineCount} line{lineCount !== 1 ? "s" : ""}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            aria-label="Copy code"
            className="rounded-md border code-button-border code-button-bg px-2 py-1 text-xs font-medium code-button-text hover:bg-slate-50 dark:hover:bg-slate-600 active:scale-[0.99] transition"
            onClick={() => navigator.clipboard.writeText(raw)}
          >
            Copy
          </button>
        </div>
      </div>

      {/* Body (Code) */}
      <div className="relative">
        <div
          className={`overflow-auto ${wrap ? "whitespace-pre-wrap" : ""}`}
          dangerouslySetInnerHTML={{ __html: html }}
        />
      </div>
    </div>
  );
}
