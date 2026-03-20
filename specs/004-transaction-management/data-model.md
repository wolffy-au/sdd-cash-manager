# Data Model: Transaction Management

## Transaction
- **Purpose:** Represents a double-entry transfer between two accounts along with descriptive metadata.
- **Fields:**
  - `id` (UUID, PK)
  - `action` (enum: BUY, SELL, TRANSFER, ADJUSTMENT, etc.)
  - `description` (string <= 200)
  - `memo` (string <= 500)
  - `amount` (decimal, quantized to the account currency)
  - `currency` (ISO 4217 code)
  - `date` (timestamp)
  - `status` (enum: PROCESSING_STATUS / RECONCILIATION_STATUS per spec)
  - `debit_account_id`, `credit_account_id` (FKs to Account)
  - `reconciled` (boolean)
- **Relationships:** Links both debit and credit accounts; referenced by QuickFillTemplate candidates and DuplicateCandidate groups.

## QuickFillTemplate
- **Purpose:** Captures a reusable pattern extracted from historical transactions.
- **Fields:**
  - `id` (UUID)
  - `action`, `currency`, `description_hint`, `memo_hint`
  - `debit_account_id`, `credit_account_id`
  - `amount_hint` (decimal range or exact value)
  - `confidence` (computed score based on recency and frequency)
  - `last_used_at` (timestamp)
- **Usage:** Ranked in-memory when generating suggestions for the register view.

## DuplicateCandidate
- **Purpose:** Represents matching transactions earmarked for potential consolidation during cleanup.
- **Fields:**
  - `id` (UUID)
  - `transaction_ids` (array of UUIDs)
  - `scope` (enum: ACCOUNT, GROUP)
  - `match_fields` (json listing amount/date/account matches)
  - `status` (enum: REVIEW_PENDING, MERGED, REJECTED)
  - `suggested_canonical_id` (UUID)
  - `resolved_at` (timestamp)
- **Behavior:** Candidate resolution either merges entries atomically or retains them with a rejection log.

## AccountMergePlan
- **Purpose:** Captures a pending merge of two accounts along with structural constraints.
- **Fields:**
  - `id` (UUID)
  - `source_account_id`, `target_account_id`
  - `validation_state` (enum: VALID, DEPTH_LIMIT_EXCEEDED, CHILD_CONFLICT)
  - `child_reparent_map` (JSON describing how children move)
  - `audit_log` (text blob)
  - `created_at`, `completed_at`
- **Constraints:** Depth validation ensures merged hierarchies do not exceed five levels; merges are logged for reconciliation reference.
