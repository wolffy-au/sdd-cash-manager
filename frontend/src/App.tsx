import React from 'react';
import LedgerFeature from './features/ledger';
import './styles/layout.css';

const App: React.FC = () => (
  <div className="app-shell">
    <header className="app-shell__header">
      <p className="app-shell__intro">SDD Cash Manager UI Makeover</p>
      <p className="app-shell__subtitle">Modernized ledger + reconciliation workspaces.</p>
    </header>
    <main className="app-shell__grid">
      <LedgerFeature />
      <section className="app-shell__panel">Reconciliation workspace & insights coming next.</section>
    </main>
  </div>
);

export default App;
