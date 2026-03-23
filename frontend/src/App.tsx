import React from 'react';
import LedgerFeature from './features/ledger';
import ReconciliationFeature from './features/reconciliation';
import './styles/layout.css';

const App: React.FC = () => (
  <div className="app-shell">
    <header className="app-shell__header">
      <p className="app-shell__intro">SDD Cash Manager UI Makeover</p>
      <p className="app-shell__subtitle">Modernized ledger + reconciliation workspaces.</p>
    </header>
    <main className="app-shell__grid">
      <section className="app-shell__panel">
        <h1>Ledger Workspace</h1>
        <LedgerFeature />
      </section>
      <section className="app-shell__panel">
        <h1>Reconciliation Kit</h1>
        <ReconciliationFeature />
      </section>
    </main>
  </div>
);

export default App;
