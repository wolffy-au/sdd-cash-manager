import React, { useMemo, useState } from 'react';
import SessionControls from '../components/reconciliation/SessionControls';
import UnreconciledList from '../components/reconciliation/UnreconciledList';
import { useReconciliationStore } from '../stores/reconciliationStore';
import { useReconciliationViewModel } from '../hooks/useReconciliationViewModel';
import { ReconciliationTransaction, DifferencePayload } from '../types';

const sampleDifference: DifferencePayload = {
  amount: 120.5,
  difference_status: 'under',
  remaining_uncleared: 3,
  guidance_text: 'Review missing transactions and uncleared balances.'
};

const sampleTransactions: ReconciliationTransaction[] = Array.from({ length: 8 }, (_, index) => ({
  id: `recon-${index}`,
  date: `2026-03-${index + 1}`,
  description: `Statement ${index + 1}`,
  amount: index % 2 === 0 ? 220 : -110,
  status: index % 3 === 0 ? 'UNCLEARED' : 'CLEARED',
  processing_status: 'COMPLETED'
}));

const ReconciliationFeature: React.FC = () => {
  const { difference, statusTotals, filteredRows, toggleSelection } = useReconciliationViewModel();
  const [statementBalance, setStatementBalance] = useState('0');
  const { commands } = useReconciliationStore();

  const badgeColor = useMemo(() => {
    if (difference.difference_status === 'balanced') return 'badge-balanced';
    if (difference.difference_status === 'over') return 'badge-over';
    return 'badge-under';
  }, [difference.difference_status]);

  const handleFetchSessions = () => commands.fetchSessions('session-1');
  const handleFetchUnreconciled = () => commands.fetchUnreconciled('session-1', sampleDifference, sampleTransactions);

  return (
    <section className="reconciliation" data-testid="reconciliation-feature">
      <SessionControls
        statementBalance={statementBalance}
        onBalanceChange={setStatementBalance}
        onFetchSessions={handleFetchSessions}
        onFetchUnreconciled={handleFetchUnreconciled}
      />
      <div className="reconciliation__badge" data-testid="difference-badge">
        Difference: <span className={badgeColor}>{difference.amount.toFixed(2)}</span>
        <p>{difference.guidance_text}</p>
      </div>
      <div className="reconciliation__status">
        <span>UNCLEARED: {statusTotals.UNCLEARED}</span>
        <span>CLEARED: {statusTotals.CLEARED}</span>
        <span>RECONCILED: {statusTotals.RECONCILED}</span>
      </div>
      <UnreconciledList rows={filteredRows} onToggle={toggleSelection} />
    </section>
  );
};

export default ReconciliationFeature;
