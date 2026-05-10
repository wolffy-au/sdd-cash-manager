import React, { useState } from 'react';
import LedgerFeature from './features/ledger';
import ReconciliationFeature from './features/reconciliation';
import './styles/layout.css';

const App: React.FC = () => {
  const [showReconciliation, setShowReconciliation] = useState(false);

  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <p className="app-shell__intro">SDD Cash Manager</p>
      </header>
      <main className="app-shell__grid">
        <section className="app-shell__panel app-shell__panel--flush">
          <LedgerFeature
            onReconcile={() => setShowReconciliation(v => !v)}
            reconcileActive={showReconciliation}
          />
        </section>
        {showReconciliation && (
          <section className="app-shell__panel">
            <div className="recon-panel-header">
              <span className="recon-panel-header__title">Reconciliation</span>
              <button
                className="recon-panel-header__close"
                onClick={() => setShowReconciliation(false)}
                aria-label="Close reconciliation panel"
              >
                ✕
              </button>
            </div>
            <ReconciliationFeature />
          </section>
        )}
      </main>
    </div>
  );
};

export default App;
