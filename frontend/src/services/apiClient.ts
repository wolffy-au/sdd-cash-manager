import axios from 'axios';
import { AccountNode, DifferencePayload, ReconciliationTransaction } from '../types';

const backend = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 15_000
});

export const fetchAccounts = () => backend.get<{accounts: AccountNode[]}>('/accounts');
export const fetchSession = () => backend.get('/reconciliation/sessions');
export const fetchUnreconciled = (sessionId: string) =>
  backend.get<{transactions: ReconciliationTransaction[]; difference: DifferencePayload}>(
    '/reconciliation/sessions/unreconciled',
    { params: { session_id: sessionId } }
  );
export const applySelection = (sessionId: string, selectedIds: string[]) =>
  backend.post<DifferencePayload>(`/reconciliation/sessions/${sessionId}/transactions`, { selected_ids: selectedIds });
