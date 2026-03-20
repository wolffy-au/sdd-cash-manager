# Research Notes: Transaction Management

## Decision: Enforce double-entry ledger for every user transaction
- **Rationale:** Section 2 of `PROJECT_SPECIFICATION.md` treats double-entry accounting as mandatory, and our API already exposes debit/credit accounts; enforcing this at the API/service layer prevents invalid states downstream.
- **Alternatives considered:** Allowing single-entry transactions as optional (per earlier note) was rejected because it would compromise reconciliation accuracy and duplicate detection consistency.

## Decision: QuickFill suggestions reuse recent transactions
- **Rationale:** The feature improves speed for repeat entries without adding new persistence layers; deriving templates from the most recent successful entries keeps the matching scope bounded and performant.
- **Alternatives considered:** Building a curated template store or machine-learning predictor was deemed overkill for the current iteration.

## Decision: Duplicate detection runs at account and group scope with manual confirmation
- **Rationale:** The spec explicitly calls for both account-level and group-level consolidation; surfacing candidates for user review avoids accidentally merging semantically distinct entries.
- **Alternatives considered:** Auto-merging detected duplicates was rejected to preserve trust and auditability.
