import { useMemo } from 'react';
import { useReconciliationStore } from '../stores/reconciliationStore';

export const useReconciliationViewModel = () => {
  const {
    unreconciled,
    difference,
    selectedIds,
    commands: { applySelection }
  } = useReconciliationStore();

  const statusTotals = useMemo(() => {
    const tally = { UNCLEARED: 0, CLEARED: 0, RECONCILED: 0 } as Record<string, number>;
    unreconciled.forEach((tx) => (tally[tx.status] += 1));
    return tally;
  }, [unreconciled]);

  const filteredRows = useMemo(() =>
    unreconciled.map((tx) => ({
      ...tx,
      isSelected: selectedIds.has(tx.id)
    })),
    [selectedIds, unreconciled]
  );

  const toggleSelection = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    applySelection([...next]);
  };

  return { difference, statusTotals, filteredRows, toggleSelection };
};
