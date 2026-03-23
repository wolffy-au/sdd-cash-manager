import React from 'react';
import { ReconciliationTransaction } from '../../types';

type Props = {
  rows: (ReconciliationTransaction & { isSelected: boolean })[];
  onToggle: (id: string) => void;
};

const statusClasses = {
  UNCLEARED: 'status-amber',
  CLEARED: 'status-green',
  RECONCILED: 'status-teal'
};

const UnreconciledList: React.FC<Props> = ({ rows, onToggle }) => (
  <div className="unreconciled" data-testid="unreconciled-list">
    <ul>
      {rows.map((row) => (
        <li key={row.id} className="unreconciled__row">
          <label>
            <input type="checkbox" checked={row.isSelected} onChange={() => onToggle(row.id)} />
            <span className="unreconciled__description">{row.description}</span>
          </label>
          <span className={['unreconciled__status', statusClasses[row.status]].join(' ')}>{row.status}</span>
          <span>{row.amount.toFixed(2)}</span>
        </li>
      ))}
    </ul>
  </div>
);

export default UnreconciledList;
