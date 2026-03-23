import React from 'react';
import { DifferencePayload } from '../../types';

type Props = {
  difference: DifferencePayload;
  onFilterUncleared: () => void;
};

const statusCopy: Record<DifferencePayload['difference_status'], { label: string; icon: string; actionLabel: string; badgeClass: string }> = {
  balanced: {
    label: 'Balanced',
    icon: '✅',
    actionLabel: 'Review ledger history',
    badgeClass: 'insight-balanced'
  },
  under: {
    label: 'Difference under target',
    icon: '⚠️',
    actionLabel: 'Highlight UNCLEARED rows',
    badgeClass: 'insight-under'
  },
  over: {
    label: 'Difference over target',
    icon: '⚠️',
    actionLabel: 'Highlight UNCLEARED rows',
    badgeClass: 'insight-over'
  }
};

const DiscrepancyInsight: React.FC<Props> = ({ difference, onFilterUncleared }) => {
  const { label, icon, actionLabel, badgeClass } = statusCopy[difference.difference_status];

  return (
    <section className={`discrepancy-insight ${badgeClass}`} data-testid="discrepancy-insight">
      <div className="discrepancy-insight__header">
        <span className="discrepancy-insight__icon" aria-hidden="true">
          {icon}
        </span>
        <div>
          <p className="discrepancy-insight__title">{label}</p>
          <p className="discrepancy-insight__subtitle">Remaining: {difference.remaining_uncleared}</p>
        </div>
        <span className="discrepancy-insight__amount">{difference.amount.toFixed(2)}</span>
      </div>
      <p className="discrepancy-insight__guidance">{difference.guidance_text}</p>
      {difference.remaining_uncleared > 0 && (
        <button type="button" className="discrepancy-insight__action" onClick={onFilterUncleared}>
          {actionLabel}
        </button>
      )}
    </section>
  );
};

export default DiscrepancyInsight;
