import React from 'react';
import { LedgerRow } from '../../types';

type Props = {
  rows: LedgerRow[];
  onSelect: (id: string) => void;
};

const fmt = (n: number): string =>
  Math.abs(n).toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const reconciledLabel = (r?: string) => {
  if (r === 'y') return 'R';
  if (r === 'c') return 'c';
  return '';
};

const Register: React.FC<Props> = ({ rows, onSelect }) => (
  <div className="register" data-testid="register">
    <table className="register-table">
      <thead>
        <tr>
          <th className="register-col--date">Date</th>
          <th className="register-col--num">Num</th>
          <th className="register-col--desc">Description</th>
          <th className="register-col--transfer">Transfer</th>
          <th className="register-col--r">R</th>
          <th className="register-col--amount">Amount</th>
          <th className="register-col--balance">Balance</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(row => (
          <tr key={row.id} className="register-row" onClick={() => onSelect(row.id)}>
            <td className="register-row__date">{row.date}</td>
            <td className="register-row__num">{row.num ?? ''}</td>
            <td className="register-row__desc">{row.description}</td>
            <td className="register-row__transfer">{row.transfer ?? ''}</td>
            <td className="register-row__r">{reconciledLabel(row.reconciled)}</td>
            <td className={`register-row__amount ${row.amount < 0 ? 'balance--negative' : 'balance--positive'}`}>
              {row.amount < 0 ? '-' : ''}{fmt(row.amount)}
            </td>
            <td className={`register-row__balance ${row.balance < 0 ? 'balance--negative' : 'balance--positive'}`}>
              {row.balance < 0 ? '-' : ''}{fmt(row.balance)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export default Register;
