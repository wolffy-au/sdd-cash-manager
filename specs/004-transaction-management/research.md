# Research Notes: Transaction Management Planning

## QuickFill matching & ranking
**Decision:** Build QuickFill candidates from the most recent transactions filtered by matching `action` and `currency`, prioritizing higher confidence based on recency and frequency. Store metadata (accounts, amount range, memo fragments) so the suggestion engine can emit a single high-confidence template per typing session.
**Rationale:** The spec demands QuickFill surface the best match for the current `action`/`currency` pair while allowing edits before persistence. Recency plus frequency gives an intuitive measure of confidence without complicated machine learning.
**Alternatives considered:** Using similarity scoring on descriptions or NLP-based clustering was rejected because it introduces extra infrastructure and could violate the “manual confirmation” requirement.

## Duplicate detection scope & performance
**Decision:** Run duplicate detection within account and account-group boundaries by comparing account IDs, amounts, dates (normalized to ISO date), and optional metadata (description, memo). Use deterministic snapshots (query current data into memory) to ensure consistent reporting, and limit scan batches to existing API query limits to meet the 3-second scanning target.
**Rationale:** Exact matching minimizes false positives, respects the requirement not to auto-merge ambiguous metadata matches, and keeps the scan fast enough for 1,000 transactions.
**Alternatives considered:** Fuzzy matching (similar amounts/dates) was dismissed because the specification explicitly requires “identical entries” and flagged transactions for manual review before consolidation.

## Account merge depth validation
**Decision:** When merging, traverse the hierarchy starting from the source account to compute new depth for each child relative to the target. Reject merges that would exceed the 5-level limit, or alternatively reparent children to intermediate nodes if safe (while documenting the reasoning in the audit log).
**Rationale:** The spec explicitly mentions guarding against merges that would breach the hierarchy depth constraint. Early validation avoids inconsistent state by rejecting unsafe merges up front.
**Alternatives considered:** Automatically flattening the hierarchy or collapsing nodes was rejected because it obscures existing structures and could contradict the requirement to preserve balances and logs.
