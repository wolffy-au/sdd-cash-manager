import { useState, useRef, useCallback } from 'react';

const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));

export const useSplitPane = (
  storageKey: string,
  defaultPx: number,
  min = 160,
  max = 700
) => {
  const [width, setWidth] = useState<number>(() => {
    const raw = localStorage.getItem(storageKey);
    const parsed = raw ? parseInt(raw, 10) : NaN;
    return Number.isFinite(parsed) ? clamp(parsed, min, max) : defaultPx;
  });

  const startX = useRef(0);
  const startWidth = useRef(0);

  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      startX.current = e.clientX;
      startWidth.current = width;
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';

      const onMove = (ev: MouseEvent) => {
        setWidth(clamp(startWidth.current + ev.clientX - startX.current, min, max));
      };

      const onUp = (ev: MouseEvent) => {
        const final = clamp(startWidth.current + ev.clientX - startX.current, min, max);
        localStorage.setItem(storageKey, String(final));
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      };

      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    },
    [width, storageKey, min, max]
  );

  return { width, onMouseDown };
};
