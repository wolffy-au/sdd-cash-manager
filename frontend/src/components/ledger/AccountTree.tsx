import React, { useState } from 'react';
import { AccountNode } from '../../types';

type Props = {
  tree: AccountNode[];
  selectedAccountId: string | null;
  onSelect: (id: string) => void;
  onOpen: (id: string) => void;
};

type FlatRow = {
  node: AccountNode;
  depth: number;
  hasChildren: boolean;
};

const getAllIds = (nodes: AccountNode[]): string[] =>
  nodes.flatMap(n => [n.id, ...(n.children ? getAllIds(n.children) : [])]);

const flattenTree = (nodes: AccountNode[], depth: number, expanded: Set<string>): FlatRow[] =>
  nodes.flatMap(node => {
    const hasChildren = !!(node.children?.length);
    const row: FlatRow = { node, depth, hasChildren };
    if (hasChildren && expanded.has(node.id)) {
      return [row, ...flattenTree(node.children!, depth + 1, expanded)];
    }
    return [row];
  });

const fmt = (n: number): string =>
  Math.abs(n).toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const AccountTree: React.FC<Props> = ({ tree, selectedAccountId, onSelect, onOpen }) => {
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set(getAllIds(tree)));

  const toggle = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpanded(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const rows = flattenTree(tree, 0, expanded);
  const total = tree.reduce((s, n) => s + n.balance, 0);

  return (
    <div className="account-tree" data-testid="account-tree">
      <table className="account-table">
        <thead>
          <tr>
            <th className="account-col--name">Account Name</th>
            <th className="account-col--type">Type</th>
            <th className="account-col--code">Account Code</th>
            <th className="account-col--balance">Total</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ node, depth, hasChildren }) => {
            const isSelected = node.id === selectedAccountId;
            const isExpanded = expanded.has(node.id);
            return (
              <tr
                key={node.id}
                className={[
                  'account-row',
                  isSelected ? 'account-row--selected' : '',
                  node.placeholder ? 'account-row--group' : '',
                ].filter(Boolean).join(' ')}
                onClick={() => onSelect(node.id)}
                onDoubleClick={() => !node.placeholder && onOpen(node.id)}
              >
                <td className="account-row__name-cell">
                  <span
                    className="account-row__indent"
                    style={{ width: depth * 18 + 'px' }}
                  />
                  {hasChildren ? (
                    <button
                      className="account-row__toggle"
                      onClick={e => toggle(node.id, e)}
                      aria-label={isExpanded ? 'Collapse' : 'Expand'}
                    >
                      {isExpanded ? '▾' : '▸'}
                    </button>
                  ) : (
                    <span className="account-row__toggle account-row__toggle--leaf" />
                  )}
                  <span className="account-icon" aria-hidden="true">
                    <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                      <rect x="1" y="5.5" width="11" height="6.5" rx="1" stroke="currentColor" strokeWidth="1.1" />
                      <path d="M2.5 5.5V4.5a4 4 0 0 1 8 0v1" stroke="currentColor" strokeWidth="1.1" />
                      <rect x="4.5" y="8" width="4" height="4" rx="0.5" fill="currentColor" opacity="0.55" />
                    </svg>
                  </span>
                  <span className="account-row__label">{node.name}</span>
                </td>
                <td className="account-row__type">{node.placeholder ? '' : node.type}</td>
                <td className="account-row__code">{node.code ?? ''}</td>
                <td className={`account-row__balance ${node.balance < 0 ? 'balance--negative' : 'balance--positive'}`}>
                  {fmt(node.balance)}
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr className="account-grand-total">
            <td colSpan={3}>Grand Total:</td>
            <td className={`account-row__balance ${total < 0 ? 'balance--negative' : 'balance--positive'}`}>
              {fmt(total)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
};

export default AccountTree;
