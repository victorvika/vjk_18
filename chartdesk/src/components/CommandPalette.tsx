import { useEffect, useMemo, useRef, useState } from 'react';

export type Command = { id: string; label: string; hint?: string; run: () => void };

type Props = {
  open: boolean;
  onClose: () => void;
  commands: Command[];
};

export default function CommandPalette({ open, onClose, commands }: Props) {
  const [query, setQuery] = useState('');
  const [cursor, setCursor] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    return commands.filter((c) => `${c.label} ${c.hint ?? ''}`.toLowerCase().includes(q));
  }, [commands, query]);

  useEffect(() => {
    if (open) {
      setQuery('');
      setCursor(0);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setCursor((c) => Math.min(c + 1, results.length - 1));
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setCursor((c) => Math.max(c - 1, 0));
      }
      if (e.key === 'Enter') {
        const cmd = results[cursor];
        if (cmd) {
          cmd.run();
          onClose();
        }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, results, cursor, onClose]);

  if (!open) return null;

  return (
    <div className="palette-backdrop" role="dialog" aria-modal="true" aria-label="Command palette" onClick={onClose}>
      <div className="palette" onClick={(e) => e.stopPropagation()}>
        <input
          ref={inputRef}
          value={query}
          placeholder="Search symbols, timeframes, indicators…"
          onChange={(e) => {
            setQuery(e.target.value);
            setCursor(0);
          }}
          aria-label="Command search"
        />
        <ul role="listbox">
          {results.map((c, i) => (
            <li
              key={c.id}
              role="option"
              aria-selected={i === cursor}
              className={i === cursor ? 'active' : ''}
              onMouseEnter={() => setCursor(i)}
              onClick={() => {
                c.run();
                onClose();
              }}
            >
              <span>{c.label}</span>
              {c.hint && <kbd>{c.hint}</kbd>}
            </li>
          ))}
          {!results.length && <li className="muted">No matches</li>}
        </ul>
        <footer>
          <span>↑↓ navigate</span>
          <span>↵ run</span>
          <span>esc close</span>
        </footer>
      </div>
    </div>
  );
}
