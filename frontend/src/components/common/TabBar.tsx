import React from 'react';

export type TabEntry = {
  id: string;
  label: string;
  closeable?: boolean;
};

type Props = {
  tabs: TabEntry[];
  activeId: string;
  onSelect: (id: string) => void;
  onClose: (id: string) => void;
};

const TabBar: React.FC<Props> = ({ tabs, activeId, onSelect, onClose }) => (
  <div className="tab-bar" role="tablist">
    {tabs.map(tab => (
      <div
        key={tab.id}
        role="tab"
        aria-selected={tab.id === activeId}
        className={`tab${tab.id === activeId ? ' tab--active' : ''}`}
        onClick={() => onSelect(tab.id)}
      >
        <span className="tab__label">{tab.label}</span>
        {tab.closeable && (
          <button
            className="tab__close"
            onClick={e => { e.stopPropagation(); onClose(tab.id); }}
            aria-label={`Close ${tab.label}`}
          >
            ✕
          </button>
        )}
      </div>
    ))}
  </div>
);

export default TabBar;
