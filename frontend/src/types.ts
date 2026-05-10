export type AccountNode = {
  id: string;
  name: string;
  type: string;
  code?: string;
  balance: number;
  placeholder?: boolean;
  children?: AccountNode[];
};

export type LedgerRow = {
  id: string;
  date: string;
  num?: string;
  description: string;
  transfer?: string;
  reconciled?: 'n' | 'c' | 'y';
  amount: number;
  balance: number;
};

export type ReconciliationTransaction = {
  id: string;
  date: string;
  description: string;
  amount: number;
  status: 'UNCLEARED' | 'CLEARED' | 'RECONCILED';
  processing_status: 'PENDING' | 'COMPLETED' | 'FAILED';
};

export type DifferencePayload = {
  amount: number;
  difference_status: 'balanced' | 'under' | 'over';
  remaining_uncleared: number;
  guidance_text: string;
};
