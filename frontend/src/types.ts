export type AccountNode = {
  id: string;
  name: string;
  balance: number;
  children?: AccountNode[];
};

export type LedgerRow = {
  id: string;
  description: string;
  amount: number;
  date: string;
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
