import React from 'react';
import { AccountNode } from '../../types';

type Props = {
  tree: AccountNode[];
  selectedAccountId: string | null;
  onSelect: (id: string) => void;
};

const renderNode = (
  node: AccountNode,
  depth: number,
  selectedId: string | null,
  onSelect: (id: string) => void
) => {
  const classes = ['account-node', 'depth-' + depth];
  if (selectedId === node.id) classes.push('selected');
  return (
    <div
      key={node.id}
      className={classes.join(' ')}
      style={{ paddingLeft: depth * 12 }}
      onClick={() => onSelect(node.id)}
    >
      <span className="account-node__name">{node.name}</span>
      <span className="account-node__balance">{node.balance.toFixed(2)}</span>
      {node.children?.map((child) => renderNode(child, depth + 1, selectedId, onSelect))}
    </div>
  );
};

const AccountTree: React.FC<Props> = ({ tree, selectedAccountId, onSelect }) => (
  <div className="account-tree" data-testid="account-tree">
    {tree.map((node) => renderNode(node, 0, selectedAccountId, onSelect))}
  </div>
);

export default AccountTree;
