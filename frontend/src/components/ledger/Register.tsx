import React from 'react';
import { LedgerRow } from '../../types';
import { useVirtualizedList } from '../../hooks/useVirtualizedList';

type Props = {
  rows: LedgerRow[];
  onSelect: (id: string) => void;
};

const Register: React.FC<Props> = ({ rows, onSelect }) => {
  const { visible, prev, next, start } = useVirtualizedList(rows, 8);

  return (
  <div className="register" data-testid="register">
    <div className="register__controls">
      <button type="button" onClick={prev} disabled={start === 0}>
        Prev
      </button>
      <button type="button" onClick={next} disabled={start + visible.length >= rows.length}>
        Next
      </button>
    </div>
    <ul>
      {visible.map((row) => (
        <li key={row.id} className="register__row" onClick={() => onSelect(row.id)}>
          <span>{row.date}</span>
          <span>{row.description}</span>
          <span>{row.amount.toFixed(2)}</span>
        </li>
      ))}
    </ul>
  </div>
  );
};

export default Register;
