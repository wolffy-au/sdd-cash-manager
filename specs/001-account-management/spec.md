## Functional Requirement to Task Mapping

| Requirement Key | Has Task? | Task IDs                                                              | Notes                                                                                                |
| :-------------- | :-------- | :-------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------- |
| FR-001          | Yes       | T010, T011, T013, T014, T015, T016, T017, T018, T019                    | Core account creation/management.                                                                    |
| FR-002          | Yes       | T012, T017                                                            | Account types and enums defined. Ensure all defined AccountCategoryType and BankingAccountType are covered by T012 and T017. |
| FR-003          | Yes       | T011, T013, T025, T026, T029, T034                                    | Running and reconciled balances.                                                                     |
| FR-004          | Yes       | T011, T025, T026, T029                                                | Historical running balances. Clarify data fields in Transaction model: e.g., transaction\_running\_balance (after), historical\_running\_balance (prior). Differentiate from Account's available balance. |
| FR-005          | Yes       | T011                                                                  | Account notes.                                                                                       |
| FR-006          | Yes       | T031, T032, T035, T036, T037                                          | Hierarchical accounts.                                                                               |
| FR-007          | Yes       | T032, T034, T036                                                      | Parent account group balances computed on-demand. Specify mechanism: recursively sum child running balances. Performance targets: <100ms for up to 5 levels. |
| FR-008          | Yes       | T014, T016, T018, T019                                                | Account search by name.                                                                              |
| FR-009          | Yes       | T038                                                                  | Application state management for unsaved changes.                                                    |
| FR-010          | Yes       | T023, T027, T029, T030                                                | Manual balance adjustment interface. This involves a user-facing window to set new balances, trigger transactions, and update account states. |
| FR-011          | Yes       | T022, T023, T028, T029                                                | Automatic transaction creation upon adjustment.                                                      |
| FR-012          | Yes       | T022, T023, T029                                                      | Adjustment transaction amount calculation.                                                           |
| FR-013          | Yes       | T023, T028, T029, T030                                                | Transaction update to ledger/reconciliation views.                                                   |

## User Story to Task Mapping

| User Story Key | Task IDs                                                              | Notes                                                                                                |
| :------------- | :-------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------- |
| US1            | T010, T011, T012, T013, T014, T015, T016, T017, T018, T019                    | Account Creation and Management.                                                                     |
| US2            | T031, T032, T034, T035, T036, T037                                    | Hierarchical Account Structure.                                                                      |
| US3            | T020, T021, T022, T023, T025, T026, T027, T028, T029, T030                    | Balance Adjustment.                                                                                  |


## Non-Functional Requirements

- **Performance:** API endpoint response times must be under 200ms, aiming for <100ms for typical operations. The system must support at least 1000 transactions per minute under normal load.
- **Scalability:** Account retrieval for hierarchies up to 5 levels deep must complete within 200ms.
- **Accuracy & Reliability:** High degree of accuracy in all financial calculations and data integrity.

## Terminology Definitions

- **Running Balance:** The current balance reflecting all entered transactions.
- **Reconciled Balance:** The balance reflecting only transactions that have been cleared or formally reconciled against external statements.
- **Available Balance:** The readily available balance, which may differ from the running balance due to holds or pending transactions.
- **Account Group:** An Account used to aggregate the balances of its child accounts, creating a hierarchical view.
