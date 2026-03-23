import React from 'react';
import './styles/layout.css';

const App: React.FC = () => (
  <div className="app-shell">
    <header className="app-shell__header">
      <p className="app-shell__intro">SDD Cash Manager UI Makeover</p>
      <p className="app-shell__subtitle">Ledger + reconciliation workspaces coming soon.</p>
    </header>
    <main className="app-shell__grid">
      <section className="app-shell__panel">Ledger workspace placeholder</section>
      <section className="app-shell__panel">Reconciliation workspace placeholder</section>
    </main>
  </div>
);

export default App;
