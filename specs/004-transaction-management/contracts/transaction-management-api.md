# API Contracts: Transaction Management

## Transactions
- **POST /transactions/**
  - Request: `transfer_from`, `transfer_to`, `action`, `amount`, `currency`, optional `description`/`memo`, `date` (default now).
  - Response: `201 Created` with canonical transaction id and linked debit/credit entries.
  - Validation: rejects if accounts are archived/deleted, action missing, amount ≤ 0, or double-entry would break hierarchy depth.

## QuickFill
- **GET /quickfill/**
  - Query params: `action`, `currency`, `query` (partial memo/description).
  - Response: Single template object containing suggested `transfer_from`, `transfer_to`, `action`, `amount`, `memo`, and `confidence_score`.
  - Behavior: Must not mutate balances until the client confirms via POST.
- **POST /quickfill/templates/{template_id}/approve**
  - Marks the template as approved; only approved templates surface to production users.

## Duplicate Detection
- **GET /duplicates/**
  - Query params: `scope` (`account` or `group`), `account_id`, `group_id` optional.
  - Response: List of `DuplicateCandidate` records with `matching_transaction_ids`, `amount`, `date`, `description`, `confidence`, and `recommended_action` (`merge`, `dismiss`).
- **POST /duplicates/merge**
  - Body: `candidate_id`, optional `preserve_audit`. Performs safe consolidation under admin control; returns before/after balance snapshots.

## Account Merges
- **POST /accounts/merge**
  - Body: `source_account_id`, `target_account_id`, optional `reparenting_map`, `audit_notes`.
  - Response: Audit summary with `moves` list and confirmation that aggregate balances remained stable.
  - Rejection: Returns `400` if the merge would exceed the 5-level hierarchy constraint or encounter locked child accounts.
