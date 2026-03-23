import React from 'react';

type Props = {
  statementBalance: string;
  onBalanceChange: (value: string) => void;
  onFetchSessions: () => void;
  onFetchUnreconciled: () => void;
};

const SessionControls: React.FC<Props> = ({ statementBalance, onBalanceChange, onFetchSessions, onFetchUnreconciled }) => (
  <div className="session-controls" data-testid="session-controls">
    <label>
      Statement Balance
      <input type="number" value={statementBalance} onChange={(event) => onBalanceChange(event.target.value)} />
    </label>
    <div className="session-controls__actions">
      <button type="button" onClick={onFetchSessions}>
        Start Session
      </button>
      <button type="button" onClick={onFetchUnreconciled}>
        Fetch Unreconciled
      </button>
    </div>
  </div>
);

export default SessionControls;
