# Quickstart: Transaction Management

1. **Record a double-entry transaction**
   - POST `/transactions/` with payload `{ "transfer_from": "account-id-A", "transfer_to": "account-id-B", "action": "Transfer", "amount": 125.00, "currency": "USD", "description": "Fund transfer", "memo": "Settled via bank" }`.
   - Expect HTTP 201 with both debit and credit entries created and the available balances for both accounts updated.

2. **Use QuickFill suggestions**
   - Begin entering a transaction using the same `action` and `currency` as a recent entry, e.g., start typing `description` that matches an existing memo.
   - GET `/quickfill/?action=Transfer&currency=USD&query=Fund` to retrieve the top template; the response includes `transfer_from`, `transfer_to`, `amount`, and `memo`. Confirm the template with a single interaction before submitting the POST.

3. **Review duplicate candidates**
   - GET `/duplicates/?scope=account&account_id={id}` to list identical entries flagged for manual consolidation.
   - POST `/duplicates/merge` with `{ "candidate_id": "…" }` to canonicalize duplicates; ensure the balance snapshots confirm no net change.

4. **Merge accounts safely**
   - POST `/accounts/merge` with `{ "source_account_id": "…", "target_account_id": "…" }` and optional reparenting map when dealing with child accounts.
   - The API validates the 5-level depth constraint and returns a summary of moved entries plus audit metadata. Any violation returns 400 with actionable instructions.

5. **Security & audits**
   - All endpoints require the standard JWT header from the existing auth flow. Merges and duplicate consolidations emit structured audit logs via `lib/security_events.py`.

Follow the spec’s success criteria to keep the responses consistent, performant, and auditable.
