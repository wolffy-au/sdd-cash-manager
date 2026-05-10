import React, { useMemo, useState } from 'react';
import AccountTree from '../components/ledger/AccountTree';
import Register from '../components/ledger/Register';
import TabBar, { TabEntry } from '../components/common/TabBar';
import LedgerToolbar from '../components/ledger/LedgerToolbar';
import { useLedgerStore } from '../stores/ledgerStore';
import { useSplitPane } from '../hooks/useSplitPane';
import { AccountNode, LedgerRow } from '../types';

/* ── Sample data ────────────────────────────────────────────── */
const sampleTree: AccountNode[] = [
  {
    id: 'acct-assets',
    name: 'Assets',
    type: 'Asset',
    balance: 46248.39,
    placeholder: true,
    children: [
      {
        id: 'acct-bank',
        name: 'Bank and Cash Accounts',
        type: 'Asset',
        balance: 28750.81,
        placeholder: true,
        children: [
          { id: 'acct-checking', name: 'Checking', type: 'Bank', code: '507941889', balance: 12430.20 },
          { id: 'acct-savings', name: 'Savings', type: 'Bank', code: '732133-567821', balance: 7180.55 },
          { id: 'acct-direct', name: 'W Direct Debits', type: 'Bank', code: '732133-567848', balance: 9140.06 },
        ],
      },
      {
        id: 'acct-investments',
        name: 'Investments',
        type: 'Asset',
        balance: 17497.58,
        placeholder: true,
        children: [
          { id: 'acct-fund-a', name: 'Australian Ethical - High Growth', type: 'Mutual Fund', balance: 9481.22 },
          { id: 'acct-fund-b', name: 'Australian Ethical - Shares', type: 'Mutual Fund', balance: 8016.36 },
        ],
      },
    ],
  },
  {
    id: 'acct-equity',
    name: 'Equity',
    type: 'Equity',
    balance: 0,
    placeholder: true,
    children: [
      { id: 'acct-opening', name: 'Opening Balances', type: 'Equity', balance: 0 },
    ],
  },
  {
    id: 'acct-expenses',
    name: 'Expenses',
    type: 'Expense',
    balance: 3812.45,
    placeholder: true,
    children: [
      { id: 'acct-groceries', name: 'Groceries', type: 'Expense', balance: 948.30 },
      { id: 'acct-utilities', name: 'Utilities', type: 'Expense', balance: 456.00 },
      { id: 'acct-dining', name: 'Dining', type: 'Expense', balance: 312.75 },
      {
        id: 'acct-auto',
        name: 'Auto',
        type: 'Expense',
        balance: 2095.40,
        placeholder: true,
        children: [
          { id: 'acct-fuel', name: 'Fuel', type: 'Expense', balance: 680.10 },
          { id: 'acct-repairs', name: 'Repair and Maintenance', type: 'Expense', balance: 1415.30 },
        ],
      },
    ],
  },
  {
    id: 'acct-income',
    name: 'Income',
    type: 'Income',
    balance: -8500.00,
    placeholder: true,
    children: [
      { id: 'acct-salary', name: 'Salary', type: 'Income', balance: -8500.00 },
    ],
  },
  {
    id: 'acct-liabilities',
    name: 'Liabilities',
    type: 'Liability',
    balance: -4280.00,
    placeholder: true,
    children: [
      { id: 'acct-cc', name: 'Credit Card', type: 'Credit Card', balance: -4280.00 },
    ],
  },
];

const sampleRows: LedgerRow[] = [
  { id: 'r0',  date: '01/04/2026', num: '',    description: 'Opening Balance',     transfer: 'Equity:Opening Balances', reconciled: 'y', amount: 12000.00, balance: 12000.00 },
  { id: 'r1',  date: '03/04/2026', num: '',    description: 'Woolworths',           transfer: 'Expenses:Groceries',      reconciled: 'y', amount: -87.45,  balance: 11912.55 },
  { id: 'r2',  date: '05/04/2026', num: '101', description: 'Council Rates',        transfer: 'Expenses:Utilities',      reconciled: 'y', amount: -456.00, balance: 11456.55 },
  { id: 'r3',  date: '08/04/2026', num: '',    description: 'Coles',                transfer: 'Expenses:Groceries',      reconciled: 'c', amount: -112.30, balance: 11344.25 },
  { id: 'r4',  date: '10/04/2026', num: '',    description: 'Salary - Stephan',     transfer: 'Income:Salary',           reconciled: 'c', amount: 4250.00, balance: 15594.25 },
  { id: 'r5',  date: '12/04/2026', num: '',    description: 'Shell Petrol',         transfer: 'Expenses:Auto:Fuel',      reconciled: 'n', amount: -95.40,  balance: 15498.85 },
  { id: 'r6',  date: '15/04/2026', num: '',    description: 'Mechanic Invoice',     transfer: 'Expenses:Auto:Repair',    reconciled: 'n', amount: -680.00, balance: 14818.85 },
  { id: 'r7',  date: '18/04/2026', num: '',    description: 'Restaurant Dinner',    transfer: 'Expenses:Dining',         reconciled: 'n', amount: -95.75,  balance: 14723.10 },
  { id: 'r8',  date: '20/04/2026', num: '',    description: 'Salary - Stephan',     transfer: 'Income:Salary',           reconciled: 'n', amount: 4250.00, balance: 18973.10 },
  { id: 'r9',  date: '22/04/2026', num: '',    description: 'Aldi',                 transfer: 'Expenses:Groceries',      reconciled: 'n', amount: -63.20,  balance: 18909.90 },
  { id: 'r10', date: '25/04/2026', num: '',    description: 'Transfer to Savings',  transfer: 'Assets:Savings',          reconciled: 'n', amount: -2000.00, balance: 16909.90 },
  { id: 'r11', date: '28/04/2026', num: '',    description: 'Credit Card Payment',  transfer: 'Liabilities:Credit Card', reconciled: 'n', amount: -500.00, balance: 16409.90 },
];

useLedgerStore.setState({ accountTree: sampleTree, registerRows: sampleRows });

/* ── Helpers ────────────────────────────────────────────────── */
const findNode = (nodes: AccountNode[], id: string): AccountNode | undefined => {
  for (const n of nodes) {
    if (n.id === id) return n;
    const found = n.children ? findNode(n.children, id) : undefined;
    if (found) return found;
  }
  return undefined;
};

/* ── Feature ────────────────────────────────────────────────── */
type Props = {
  onReconcile: () => void;
  reconcileActive: boolean;
};

type TabData = TabEntry & { type: 'accounts' | 'register' };

const ACCOUNTS_TAB: TabData = { id: 'accounts', type: 'accounts', label: 'Accounts', closeable: false };

const LedgerFeature: React.FC<Props> = ({ onReconcile, reconcileActive }) => {
  const { accountTree, registerRows, selectedAccountId, commands } = useLedgerStore();
  const { width: treeWidth, onMouseDown: onDividerDown } = useSplitPane('ledger-split-px', 390, 200, 700);

  const [tabs, setTabs] = useState<TabData[]>([ACCOUNTS_TAB]);
  const [activeTabId, setActiveTabId] = useState<string>('accounts');

  const activeTab = tabs.find(t => t.id === activeTabId) ?? ACCOUNTS_TAB;

  const selectedNode = useMemo(
    () => (selectedAccountId ? findNode(accountTree, selectedAccountId) : undefined),
    [accountTree, selectedAccountId]
  );

  const canActOnSelected = !!selectedNode && !selectedNode.placeholder;

  const openRegister = (accountId: string, name: string) => {
    const id = `reg-${accountId}`;
    setTabs(prev =>
      prev.find(t => t.id === id)
        ? prev
        : [...prev, { id, type: 'register', label: name, closeable: true }]
    );
    setActiveTabId(id);
  };

  const closeTab = (id: string) => {
    setTabs(prev => prev.filter(t => t.id !== id));
    if (activeTabId === id) setActiveTabId('accounts');
  };

  const handleOpenRegister = () => {
    if (canActOnSelected) openRegister(selectedNode!.id, selectedNode!.name);
  };

  return (
    <section className="ledger-workspace" data-testid="ledger-feature">
      <LedgerToolbar
        tabType={activeTab.type}
        canActOnSelected={canActOnSelected}
        onNew={() => {}}
        onEdit={() => {}}
        onDelete={() => {}}
        onOpenRegister={handleOpenRegister}
        onReconcile={onReconcile}
        reconcileActive={reconcileActive}
        onFilter={() => {}}
      />
      <TabBar tabs={tabs} activeId={activeTabId} onSelect={setActiveTabId} onClose={closeTab} />
      <div className="ledger-workspace__body">
        {activeTab.type === 'accounts' ? (
          <div
            className="ledger"
            style={{ gridTemplateColumns: `${treeWidth}px 6px 1fr` }}
          >
            <div className="ledger__tree-panel">
              <AccountTree
                tree={accountTree}
                selectedAccountId={selectedAccountId}
                onSelect={commands.expandAccount}
                onOpen={id => {
                  const node = findNode(accountTree, id);
                  if (node && !node.placeholder) openRegister(id, node.name);
                }}
              />
            </div>
            <div className="ledger__divider" onMouseDown={onDividerDown} />
            <div className="ledger__register-panel">
              <Register rows={registerRows} onSelect={commands.selectRow} />
            </div>
          </div>
        ) : (
          <div className="ledger__register-panel ledger__register-panel--full">
            <Register rows={registerRows} onSelect={commands.selectRow} />
          </div>
        )}
      </div>
    </section>
  );
};

export default LedgerFeature;
