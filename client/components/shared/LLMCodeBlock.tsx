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
  // react-markdown/Streamdown often pass meta via node or data-*; adapt as needed:
  // @ts-ignore
  node?: { meta?: string };
  // @ts-ignore
  "data-meta"?: string;
};

function escapeHtml(s: string) {
  return s.replace(/[&<>"']/g, (m) =>
    m === "&" ? "&amp;" :
    m === "<" ? "&lt;" :
    m === ">" ? "&gt;" :
    m === '"' ? "&quot;" : "&#39;"
  );
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

  useEffect(() => {
    let cancelled = false;

    // Initialize Mermaid for this render pass
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      // You can tune other options if needed (fontFamily, logLevel, etc.)
      theme,
    });

    (async () => {
      try {
        const { svg } = await mermaid.render(id, code);
        if (!cancelled) {
          setSvg(svg);
          setErr(null);
        }
      } catch (e: any) {
        if (!cancelled) {
          setErr(e?.message || "Failed to render diagram");
          setSvg("");
        }
      }
    })();

    return () => {
      cancelled = true;
      // Optional: reset internal cache between renders
      // mermaid.reset(); // uncomment if you hit stale state issues
    };
  }, [code, id, theme]);

  if (err) {
    return (
      <div className="p-4 text-sm text-red-600 dark:text-red-400">
        Mermaid error: {err}
        <pre className="mt-2 overflow-auto rounded bg-slate-100 dark:bg-slate-800 p-3 text-xs">
          {code}
        </pre>
      </div>
    );
  }

  if (!svg) {
    return (
      <div className="p-4 text-xs text-slate-500 dark:text-slate-400">
        Rendering diagram…
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

  // Inline: never run Shiki to avoid conflicts with single backticks
  if (inline || !/language-/.test(className || "")) {
    return (
      <code className="rounded px-1.5 py-0.5 font-mono text-[0.9em] bg-slate-200/70 dark:bg-slate-700/70 text-slate-800 dark:text-slate-200">
        {children}
      </code>
    );
  }

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
    // If you also support a manual "codeBlockTheme" override, prefer it here:
    // const preferred = codeBlockTheme || 'auto'
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
    // crude map: any "dark" -> mermaid dark, else default
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
        transformerMetaHighlight(),        // ```js {1,3-4}
        transformerMetaWordHighlight(),    // ```
      ],
      // Optional: define meta directly (if your parser doesn't pass it)
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [raw, mappedLang, meta, themeKey]);

  // UX: line count for the header badge
  const lineCount = useMemo(() => raw.split("\n").length, [raw]);

  // --- MERMAID RENDER PATH ---------------------------------------------------
  if (mappedLang === "mermaid") {
    const mermaidTheme = getMermaidTheme();

    return (
      <div className="my-4 overflow-hidden rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-lg dark:shadow-slate-900/50">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3 py-2.5">
          <div className="flex items-center gap-3">
            {showLanguageBadge && (
              <span className="rounded-md bg-slate-200 dark:bg-slate-700 px-2 py-0.5 text-xs font-semibold capitalize text-slate-700 dark:text-slate-300">
                {title || "mermaid"}
              </span>
            )}
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {lineCount} line{lineCount !== 1 ? "s" : ""}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label="Copy diagram source"
              className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-2 py-1 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600 active:scale-[0.99] transition"
              onClick={() => navigator.clipboard.writeText(raw)}
            >
              Copy source
            </button>
          </div>
        </div>

        {/* Body (Mermaid SVG) */}
        <div className="relative">
          <MermaidBlock code={raw} theme={mermaidTheme} />
        </div>
      </div>
    );
  }
  // ---------------------------------------------------------------------------

  // DEFAULT (non-Mermaid) RENDER PATH WITH SHIKI
  return (
    <div className="my-4 overflow-hidden rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-lg dark:shadow-slate-900/50">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3 py-2.5">
        <div className="flex items-center gap-3">
          {showLanguageBadge && (
            <span className="rounded-md bg-slate-200 dark:bg-slate-700 px-2 py-0.5 text-xs font-semibold capitalize text-slate-700 dark:text-slate-300">
              {title}
            </span>
          )}
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {lineCount} line{lineCount !== 1 ? "s" : ""}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            aria-label="Copy code"
            className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-2 py-1 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600 active:scale-[0.99] transition"
            onClick={() => navigator.clipboard.writeText(raw)}
          >
            Copy
          </button>
          <button
            type="button"
            aria-label="Toggle wrap"
            className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-2 py-1 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600 active:scale-[0.99] transition"
            onClick={() => setWrap((v) => !v)}
          >
            {wrap ? "No-wrap" : "Wrap"}
          </button>
        </div>
      </div>

      {/* Body */}
      <div className={`relative ${wrap ? "" : "overflow-x-auto"}`}>
        <div
          className={`p-4 text-[13px] leading-relaxed font-mono bg-transparent ${
            wrap ? "whitespace-pre-wrap break-words" : ""
          } ${showLineNumbers ? "line-numbers" : ""}`}
          dangerouslySetInnerHTML={{ __html: html }}
        />
      </div>
    </div>
  );
}
