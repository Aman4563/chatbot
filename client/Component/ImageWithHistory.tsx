import { useState, useEffect } from 'react';

interface ImageWithHistoryProps {
  src?: string;
  alt?: string;
  maxHeight?: string | number;
}

export function ImageWithHistory({ src, alt, maxHeight }: ImageWithHistoryProps) {
  const initial = (typeof src === 'string' && src.trim().length > 0) ? [src] : [];
  const [history, setHistory] = useState<string[]>(initial);
  const [currentIndex, setCurrentIndex] = useState(initial.length ? 0 : 0);

  useEffect(() => {
    if (typeof src === 'string') {
      const trimmed = src.trim();
      if (trimmed && history[history.length - 1] !== trimmed) {
        setHistory(h => [...h, trimmed]);
        setCurrentIndex(i => i + 1);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src]);

  if (history.length === 0) {
    // Prevents <img src=""> and the React warning
    return null;
  }

  const atStart = currentIndex === 0;
  const atEnd = currentIndex === history.length - 1;

  return (
    <div className="my-4 text-center">
      {history.length > 1 && (
        <div className="flex items-center justify-center gap-4 mb-2">
          <button onClick={() => setCurrentIndex(i => Math.max(i - 1, 0))} disabled={atStart} aria-label="Previous">‹</button>
          <span className="text-sm text-gray-600">{currentIndex + 1} / {history.length}</span>
          <button onClick={() => setCurrentIndex(i => Math.min(i + 1, history.length - 1))} disabled={atEnd} aria-label="Next">›</button>
        </div>
      )}

      <img
        src={history[currentIndex]}
        alt={alt || 'Generated image'}
        className="max-w-full transition-transform hover:scale-[1.02]"
        style={{ maxHeight: maxHeight || '500px', objectFit: 'contain' }}
        loading="lazy"
      />
    </div>
  );
}
