import React, { useEffect } from 'react';
import AccountTree from '../components/ledger/AccountTree';
import Register from '../components/ledger/Register';
import { useLedgerStore } from '../stores/ledgerStore';
import { AccountNode, LedgerRow } from '../types';

const sampleTree: AccountNode[] = [
  {
    id: 'acct-1',
    name: 'Assets',
    balance: 24000,
    children: [
      { id: 'acct-1-1', name: 'Checking', balance: 12000 },
      { id: 'acct-1-2', name: 'Savings', balance: 7500 }
    ]
  },
  { id: 'acct-2', name: 'Liabilities', balance: -4200 }
];

const sampleRows: LedgerRow[] = Array.from({ length: 20 }, (_, index) => ({
  id: 'row-' + index,
  description: index % 2 === 0 ? 'Invoice' : 'Payment',
  amount: index % 2 === 0 ? 230.42 : -190.17,
  date: `2026-03-${(index % 28) + 1}`
}));

const LedgerFeature: React.FC = () => {
  const { accountTree, registerRows, selectedAccountId, commands } = useLedgerStore();

  useEffect(() => {
    useLedgerStore.setState({ accountTree: sampleTree, registerRows: sampleRows });
  }, []);

  return (
    <section className="ledger" data-testid="ledger-feature">
      <div className="ledger__tree-panel">
        <h2>Accounts</h2>
        <AccountTree tree={accountTree} selectedAccountId={selectedAccountId} onSelect={commands.expandAccount} />
      </div>
      <div className="ledger__register-panel">
        <h2>Register</h2>
        <Register rows={registerRows} onSelect={commands.selectRow} />
      </div>
    </section>
  );
};

export default LedgerFeature;
