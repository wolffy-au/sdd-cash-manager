import { useMemo, useState } from 'react';

export const useVirtualizedList = <T extends unknown>(items: T[], buffer = 6) => {
  const [start, setStart] = useState(0);
  const visible = useMemo(() => items.slice(start, start + buffer), [items, start, buffer]);
  const scrollTo = (index: number) => setStart(Math.min(Math.max(index, 0), Math.max(items.length - buffer, 0)));
  const next = () => setStart((prev) => Math.min(prev + buffer, Math.max(items.length - buffer, 0)));
  const prev = () => setStart((prev) => Math.max(prev - buffer, 0));
  return { visible, start, next, prev, scrollTo };
};
