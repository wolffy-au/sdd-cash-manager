import { create } from 'zustand';
import { DifferencePayload, ReconciliationTransaction } from '../types';

type ReconciliationCommands = {
  fetchSessions: (sessionId: string) => void;
  fetchUnreconciled: (sessionId: string, difference: DifferencePayload, transactions: ReconciliationTransaction[]) => void;
  applySelection: (selection: string[]) => void;
};

export type ReconciliationStoreState = {
  activeSessionId: string | null;
  statementBalance: number;
  unreconciled: ReconciliationTransaction[];
  selectedIds: Set<string>;
  difference: DifferencePayload;
  statusFlags: Record<string, number>;
  commands: ReconciliationCommands;
};

const defaultDifference: DifferencePayload = {
  amount: 0,
  difference_status: 'balanced',
  remaining_uncleared: 0,
  guidance_text: 'Balanced'
};

export const useReconciliationStore = create<ReconciliationStoreState>((set) => ({
  activeSessionId: null,
  statementBalance: 0,
  unreconciled: [],
  selectedIds: new Set(),
  difference: defaultDifference,
  statusFlags: { pending: 0, completed: 0, failed: 0 },
  commands: {
    fetchSessions: (sessionId) =>
      set(() => ({
        activeSessionId: sessionId,
        selectedIds: new Set()
      })),
    fetchUnreconciled: (sessionId, difference, transactions) =>
      set(() => ({
        activeSessionId: sessionId,
        unreconciled: transactions,
        difference
      })),
    applySelection: (selection) =>
      set((state) => ({
        selectedIds: new Set(selection),
        difference: {
          ...state.difference,
          remaining_uncleared: Math.max(0, state.difference.remaining_uncleared - selection.length)
        }
      }))
  }
}));
