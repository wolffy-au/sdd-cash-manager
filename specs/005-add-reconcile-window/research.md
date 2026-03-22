## Transaction Filtering and Status Enforcement
- **Decision**: Filter transactions server-side to include only UNCLEARED or CLEARED reconciliation_status rows whose processing_status is PENDING or COMPLETED, and block FAILED items from being selected until their processing_status changes.
- **Rationale**: This honors the spec’s requirement to keep the window focused on actionable transactions, keeps the Difference calculation deterministic, and prevents users from marking externally failed items that could later be rolled back.
- **Alternatives considered**: Returning the full ledger and letting the client filter (rejected because it would expose busy or invalid transactions and complicate the difference logic); allowing FAILED transactions to be immediately selectable (rejected because it would break audit trails and risk double marking).

## Reconciliation API Patterns with FastAPI
- **Decision**: Use FastAPI routers with dependency-injected SQLAlchemy sessions to expose endpoints for (a) retrieving filtered unreconciled transactions, (b) posting selected transaction IDs/ending balance for recalculation, and (c) supplying a summary Difference value.
- **Rationale**: FastAPI plus dependency-injected DB sessions aligns with the existing architecture; it keeps the handler code concise, ensures we honor async semantics for latency goals, and lets tests reuse the same httpx fixtures already in tests/api.
- **Alternatives considered**: Building a monolithic command endpoint that returned raw ledger data (too wide in scope and harder to test); introducing a separate microservice (unneeded complexity for this feature).

## Difference Tracking and Status Transitions
- **Decision**: Treat the Difference field as `ending_balance - sum(selected_transactions)` while advancing each transaction’s `reconciliation_status` from UNCLEARED to CLEARED (and optionally to RECONCILED once a session is saved), ensuring persistence after the session closes.
- **Rationale**: This mirrors standard reconciliation workflows, keeps results auditable, and ties naturally into the account/transaction state machine defined in the constitution.
- **Alternatives considered**: Recording a separate reconciliation delta object without mutating transaction statuses (rejected because downstream views and services rely on reconciliation_status to calculate cleared balances); letting the client remember selections without server persistence (risked data loss if the session refreshed).
