import { create } from 'zustand';
import { AccountNode, LedgerRow } from '../types';

type LedgerCommands = {
  expandAccount: (id: string) => void;
  selectRow: (id: string) => void;
  reorderTree: (direction: 'up' | 'down') => void;
};

export type LedgerStoreState = {
  selectedAccountId: string | null;
  accountTree: AccountNode[];
  registerRows: LedgerRow[];
  isLoading: boolean;
  commands: LedgerCommands;
};

export const useLedgerStore = create<LedgerStoreState>((set) => ({
  selectedAccountId: null,
  accountTree: [],
  registerRows: [],
  isLoading: false,
  commands: {
    expandAccount: (id) =>
      set((state) => ({
        selectedAccountId: id,
        isLoading: true
      })),
    selectRow: (id) =>
      set((state) => ({
        registerRows: state.registerRows.map((row) =>
          row.id === id ? { ...row, description: `${row.description} (selected)` } : row
        )
      })),
    reorderTree: () => set((state) => ({ accountTree: [...state.accountTree].reverse(), isLoading: false }))
  }
}));

export const resetLedgerState = () =>
  useLedgerStore.setState({
    selectedAccountId: null,
    accountTree: [],
    registerRows: [],
    isLoading: false
  });
