import React from 'react';

/* ── Icons ─────────────────────────────────────────────────── */
const IcoNew = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="6.5" width="16" height="11" rx="1.5" />
    <path d="M7 6.5V5a3 3 0 0 1 6 0v1.5" />
    <line x1="10" y1="10" x2="10" y2="14" />
    <line x1="8" y1="12" x2="12" y2="12" />
  </svg>
);

const IcoEdit = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <path d="M13.5 3.5a2 2 0 0 1 2.83 2.83L6 16.5l-4 1 1-4L13.5 3.5z" />
  </svg>
);

const IcoDelete = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="5 7 5 17 15 17 15 7" />
    <line x1="3" y1="7" x2="17" y2="7" />
    <path d="M8 7V4h4v3" />
    <line x1="8" y1="10" x2="8" y2="14" />
    <line x1="12" y1="10" x2="12" y2="14" />
  </svg>
);

const IcoOpen = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="3" width="12" height="14" rx="1.5" />
    <line x1="5" y1="7" x2="11" y2="7" />
    <line x1="5" y1="10" x2="11" y2="10" />
    <line x1="5" y1="13" x2="8" y2="13" />
    <polyline points="14 10 18 10 18 18 10 18" />
    <line x1="14" y1="14" x2="18" y2="10" />
  </svg>
);

const IcoReconcile = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="3" width="16" height="14" rx="1.5" />
    <line x1="5" y1="8" x2="9" y2="8" />
    <line x1="11" y1="8" x2="15" y2="8" />
    <line x1="5" y1="12" x2="9" y2="12" />
    <polyline points="11 11 13 13 16 10" />
  </svg>
);

const IcoFilter = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="2 3 18 3 12 11 12 17 8 17 8 11" />
  </svg>
);

const IcoEnter = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="4 10 8 14 16 6" />
  </svg>
);

const IcoBlank = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="2" width="12" height="16" rx="1.5" />
    <line x1="7" y1="7" x2="13" y2="7" />
    <line x1="7" y1="10" x2="13" y2="10" />
    <line x1="7" y1="13" x2="10" y2="13" />
  </svg>
);

const IcoSchedule = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="4" width="16" height="14" rx="1.5" />
    <line x1="2" y1="8" x2="18" y2="8" />
    <line x1="6" y1="2" x2="6" y2="6" />
    <line x1="14" y1="2" x2="14" y2="6" />
    <circle cx="14" cy="14" r="3" />
    <polyline points="14 12.5 14 14 15.2 15.2" />
  </svg>
);

/* ── Toolbar primitives ─────────────────────────────────────── */
type BtnProps = {
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  active?: boolean;
};

const Btn: React.FC<BtnProps> = ({ label, icon, onClick, disabled, active }) => (
  <button
    className={`toolbar-icon-btn${active ? ' toolbar-icon-btn--active' : ''}`}
    onClick={onClick}
    disabled={disabled}
    title={label}
  >
    {icon}
    <span>{label}</span>
  </button>
);

const Sep = () => <div className="toolbar-sep" />;

/* ── Toolbar variants ───────────────────────────────────────── */
type AccountsProps = {
  canActOnSelected: boolean;
  onNew: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onOpenRegister: () => void;
  onReconcile: () => void;
  reconcileActive: boolean;
  onFilter: () => void;
};

const AccountsToolbar: React.FC<AccountsProps> = ({
  canActOnSelected, onNew, onEdit, onDelete,
  onOpenRegister, onReconcile, reconcileActive, onFilter,
}) => (
  <>
    <Btn label="New" icon={<IcoNew />} onClick={onNew} />
    <Btn label="Edit" icon={<IcoEdit />} onClick={onEdit} disabled={!canActOnSelected} />
    <Btn label="Delete" icon={<IcoDelete />} onClick={onDelete} disabled={!canActOnSelected} />
    <Sep />
    <Btn label="Open Register" icon={<IcoOpen />} onClick={onOpenRegister} disabled={!canActOnSelected} />
    <Sep />
    <Btn label="Reconcile" icon={<IcoReconcile />} onClick={onReconcile} disabled={!canActOnSelected} active={reconcileActive} />
    <Sep />
    <Btn label="Filter" icon={<IcoFilter />} onClick={onFilter} />
  </>
);

const RegisterToolbar: React.FC = () => (
  <>
    <Btn label="Enter" icon={<IcoEnter />} onClick={() => {}} disabled />
    <Btn label="Blank" icon={<IcoBlank />} onClick={() => {}} disabled />
    <Sep />
    <Btn label="Delete" icon={<IcoDelete />} onClick={() => {}} disabled />
    <Sep />
    <Btn label="Schedule" icon={<IcoSchedule />} onClick={() => {}} disabled />
  </>
);

/* ── Public component ───────────────────────────────────────── */
type Props =
  | ({ tabType: 'accounts' } & AccountsProps)
  | { tabType: 'register' };

const LedgerToolbar: React.FC<Props> = props => (
  <div className="ledger-toolbar">
    {props.tabType === 'accounts'
      ? <AccountsToolbar {...(props as AccountsProps)} />
      : <RegisterToolbar />}
  </div>
);

export default LedgerToolbar;
