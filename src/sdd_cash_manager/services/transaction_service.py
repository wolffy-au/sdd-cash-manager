from datetime import date, datetime
from decimal import Decimal  # New import
from typing import Callable

from sqlalchemy import literal, select  # New import
from sqlalchemy.orm import Session  # New import

from sdd_cash_manager.lib.security_events import log_critical_application_error  # New import
from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.duplicate_candidate import DuplicateCandidate
from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.models.quickfill_template import QuickFillTemplate
from sdd_cash_manager.models.transaction import Entry, Transaction
from sdd_cash_manager.services.account_service import AccountService

MAX_HIERARCHY_DEPTH = 5
DUPLICATE_SCAN_LIMIT = 1000

BALANCING_ACCOUNT_ID = "balancing-account-id"
FORBIDDEN_CHAR_PATTERN = r"[<>;]"


class TransactionService:
    """Manage transaction creation and persistence."""

    def __init__(self, db_session: Session | None = None, session_factory: Callable[[], Session] | None = None):
        """Initialize the transaction service with a database session or factory.

        Args:
            db_session: Optional SQLAlchemy session used for persistence.
            session_factory: Optional factory for tests that need to open isolated sessions.
        """
        self.db_session = db_session
        self.session_factory = session_factory
        self._use_db = bool(db_session or session_factory)
        self.account_service: AccountService | None = None  # Reference to AccountService

    def _acquire_session(self) -> tuple[Session, bool]:
        """Return a session plus a flag indicating whether the caller must close it."""
        try:
            if self.session_factory:
                return self.session_factory(), True
            if self.db_session is None:
                raise ValueError("Database session is required for transaction operations.")
            return self.db_session, False
        except Exception as e:
            log_critical_application_error(f"Failed to acquire database session for transaction service: {e}", metadata={"service": "TransactionService"})
            raise RuntimeError("Failed to acquire database session for transaction service due to unexpected error.") from e

    def set_account_service(self, account_service: AccountService) -> None:
        """Attach an AccountService to enable account interactions.

        Args:
            account_service: Service managing account persistence.

        Returns:
            None: Stores the provided service for future adjustments.
        """
        self.account_service = account_service

    def _build_entry(
        self,
        transaction_id: str | None, # transaction_id can be None before flush
        account_id: str,
        debit_amount: Decimal, # Changed from float to Decimal
        credit_amount: Decimal, # Changed from float to Decimal
        notes: str | None = None
    ) -> Entry:
        """Create a single ledger entry for a transaction."""
        return Entry(
            transaction_id=transaction_id,
            account_id=account_id,
            debit_amount=debit_amount,
            credit_amount=credit_amount,
            notes=notes
        )

    def _ensure_double_entry(self, entries: list[Entry]) -> None:
        """Verify that debits and credits balance across provided entries."""
        total_debits = sum((entry.debit_amount for entry in entries), start=Decimal("0"))
        total_credits = sum((entry.credit_amount for entry in entries), start=Decimal("0"))
        difference: Decimal = total_debits - total_credits
        if difference.copy_abs() > Decimal("0.00001"): # Use Decimal for comparison
            raise ValueError("Transaction entries must balance.")

    @staticmethod
    def _validate_string_field(
        value: str,
        field_name: str,
        min_length: int = 1,
        max_length: int | None = None,
        allowed_chars_regex: str | None = None,
        forbidden_chars_regex: str | None = FORBIDDEN_CHAR_PATTERN  # Default forbidden chars from spec
    ) -> str:
        import re  # Import regex

        stripped_value = value.strip()
        if len(stripped_value) < min_length:
            raise ValueError(f"{field_name} must be at least {min_length} characters long.")
        if max_length is not None and len(stripped_value) > max_length:
            raise ValueError(f"{field_name} cannot exceed {max_length} characters.")

        if forbidden_chars_regex and re.search(forbidden_chars_regex, stripped_value):
            raise ValueError(f"{field_name} contains forbidden characters: {forbidden_chars_regex}")

        if allowed_chars_regex and not re.fullmatch(allowed_chars_regex, stripped_value):
            raise ValueError(f"{field_name} contains invalid characters. Allowed pattern: {allowed_chars_regex}")

        return stripped_value


    def create_transaction(
        self,
        effective_date: datetime,
        booking_date: datetime,
        description: str,
        amount: Decimal, # Changed from float to Decimal
        debit_account_id: str,
        credit_account_id: str,
        action_type: str,
        notes: str | None = None,
        entries: list[Entry] | None = None
    ) -> Transaction:
        """Create a new transaction record backed by ledger entries and persist it."""
        # --- Validation Block ---
        # Validate description
        validated_description = self._validate_string_field(description, "description", max_length=255, forbidden_chars_regex=FORBIDDEN_CHAR_PATTERN)

        # Validate notes if present
        validated_notes = None
        if notes is not None:
            validated_notes = self._validate_string_field(notes, "notes", max_length=500, forbidden_chars_regex=FORBIDDEN_CHAR_PATTERN)

        if not debit_account_id or not credit_account_id or not action_type:
            raise ValueError("Debit account ID, credit account ID, and action type are required.")
        if debit_account_id == credit_account_id:
            raise ValueError("Debit and credit accounts cannot be the same.")
        if amount <= Decimal(0): # Use Decimal for comparison
            raise ValueError("Transaction amount must be greater than zero.")
        # --- End Validation Block ---

        ledger_entries = entries or [
            self._build_entry(None, debit_account_id, amount, Decimal(0.0), validated_notes), # transaction_id will be set by SQLAlchemy
            self._build_entry(None, credit_account_id, Decimal(0.0), amount, validated_notes), # transaction_id will be set by SQLAlchemy
        ]
        self._ensure_double_entry(ledger_entries)

        transaction = Transaction(
            effective_date=effective_date,
            booking_date=booking_date,
            description=validated_description,
            amount=amount,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            action_type=action_type,
            entries=ledger_entries, # Assign entries to trigger cascade
            notes=validated_notes,
            processing_status=ProcessingStatus.PENDING,
            reconciliation_status=ReconciliationStatus.PENDING_RECONCILIATION
        )

        session, should_close = self._acquire_session()
        try:
            session.add(transaction)
            session.flush() # Generate ID and persist entries via cascade
            session.refresh(transaction) # Reload with fresh state and IDs
            return transaction
        except Exception as e:
            log_critical_application_error(f"Failed to create transaction {transaction.description}: {e}", metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to create transaction {transaction.description} due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def get_transaction(self, transaction_id: str, *, session: Session | None = None) -> Transaction | None:
        """Retrieve a transaction by identifier from the database.

        Args:
            transaction_id: Identifier of the transaction to fetch.
            session: Optional SQLAlchemy session to use.

        Returns:
            Transaction | None: The transaction if it exists, otherwise None.
        """
        if not self._use_db:
            raise RuntimeError("TransactionService must be used with a database session to get transactions.")

        active_session = session or self.db_session
        if active_session is None:
            raise ValueError("Database session is required to retrieve transactions.")
        try:
            return active_session.get(Transaction, transaction_id)
        except Exception as e:
            log_critical_application_error(f"Failed to retrieve transaction {transaction_id}: {e}", metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to retrieve transaction {transaction_id} due to unexpected error.") from e

    def get_transactions_by_account(self, account_id: str) -> list[Transaction]:
        """Return all transactions involving the given account from the database.

        Args:
            account_id: Identifier to filter transactions.

        Returns:
            list[Transaction]: Matching transactions.
        """
        if not self._use_db:
            raise RuntimeError("TransactionService must be used with a database session to get transactions by account.")

        session, should_close = self._acquire_session()
        try:
            query = select(Transaction).where(
                (Transaction.debit_account_id == account_id) |
                (Transaction.credit_account_id == account_id)
            )
            return list(session.scalars(query).all())
        except Exception as e:
            log_critical_application_error(f"Failed to retrieve transactions for account {account_id}: {e}", account_id=account_id, metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to retrieve transactions for account {account_id} due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def update_transaction_status(
        self,
        transaction_id: str,
        processing_status: ProcessingStatus | None = None,
        reconciliation_status: ReconciliationStatus | None = None
    ) -> Transaction | None:
        """Update processing or reconciliation status for a transaction in the database.

        Args:
            transaction_id: Identifier of the transaction to update.
            processing_status: Optional new processing status.
            reconciliation_status: Optional new reconciliation status.

        Returns:
            Transaction | None: The updated transaction or None if not found.
        """
        if not self._use_db:
            raise RuntimeError("TransactionService must be used with a database session to update transaction status.")

        session, should_close = self._acquire_session()
        try:
            transaction = self.get_transaction(transaction_id, session=session) # Use the same session
            if transaction:
                if processing_status:
                    transaction.processing_status = processing_status
                if reconciliation_status:
                    transaction.reconciliation_status = reconciliation_status
                session.flush() # Persist changes
            return transaction
        except Exception as e:
            log_critical_application_error(f"Failed to update status for transaction {transaction_id}: {e}", metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to update status for transaction {transaction_id} due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def perform_balance_adjustment(
        self,
        account_id: str,
        target_balance: Decimal, # Changed from float to Decimal
        adjustment_date: datetime,
        description: str,
        action_type: str,
        notes: str | None = None
    ) -> Transaction | None:
        """Adjust an account balance by creating a balancing transaction.

        Args:
            account_id: Identifier of the account to adjust.
            target_balance: Desired balance after adjustment.
            adjustment_date: Effective datetime for the adjustment.
            description: Description used in the transaction.
            action_type: Classification of the adjustment.
            notes: Optional notes for the transaction.

        Returns:
            Transaction | None: Created adjustment transaction when a change occurred.

        Raises:
            RuntimeError: If AccountService has not been attached or unexpected database error.
            ValueError: If the account cannot be found or validation fails.
        """
        try: # Added outer try-except for critical errors
            if not self.account_service:
                raise RuntimeError("AccountService is not set.")

            account = self.account_service.get_account(account_id)
            if not account:
                raise ValueError(f"Account with ID {account_id} not found.")

            current_balance = Decimal(account.available_balance)  # Coerce to Decimal for strict typing
            amount_difference = target_balance - current_balance

            if amount_difference.copy_abs() < Decimal("0.001"):  # Use Decimal for comparison
                return None

            transaction_amount = amount_difference.copy_abs()  # This will already be Decimal
            if amount_difference < 0: # Debit account (balance decreases)
                debit_id = account_id
                credit_id = BALANCING_ACCOUNT_ID
            else: # Credit account (balance increases)
                debit_id = BALANCING_ACCOUNT_ID
                credit_id = account_id

            created_transaction = self.create_transaction(
                effective_date=adjustment_date,
                booking_date=datetime.now(),
                description=f"{description} for account {account.name}", # Use account name for clearer description
                amount=transaction_amount,
                debit_account_id=debit_id,
                credit_account_id=credit_id,
                action_type=action_type,
                notes=notes
            )

            updated_account = self.account_service.update_account(account_id, available_balance=target_balance)
            if updated_account is None:
                raise ValueError(f"Account with ID {account_id} not found.")

            self.account_service.record_balance_snapshot(
                account_id,
                timestamp=adjustment_date,
                reason=f"Balance adjustment to {target_balance}"
            )

            # Mark transaction as posted immediately for balance adjustments
            self.update_transaction_status(
                created_transaction.id,
                processing_status=ProcessingStatus.POSTED,
                reconciliation_status=ReconciliationStatus.PENDING_RECONCILIATION
            )

            return created_transaction
        except (ValueError, RuntimeError):
            raise
        except Exception as exc:
            log_critical_application_error(f"Failed to perform balance adjustment for account {account_id}: {exc}", account_id=account_id, metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to perform balance adjustment for account {account_id} due to unexpected error.") from exc

    def rank_quickfill_candidates(
        self,
        action_type: str,
        currency: str,
        query: str | None = None,
        limit: int = 5
    ) -> list[QuickFillTemplate]:
        """Rank QuickFill templates by confidence for the given action/currency pair."""
        if not self._use_db:
            raise RuntimeError("QuickFill ranking requires a database session.")

        if limit <= 0:
            limit = 5

        session, should_close = self._acquire_session()
        try:
            stmt = (
                select(QuickFillTemplate)
                .where(
                    QuickFillTemplate.action == action_type.strip(),
                    QuickFillTemplate.currency == currency.strip(),
                    QuickFillTemplate.is_approved.is_(True)
                )
                .order_by(
                    QuickFillTemplate.confidence_score.desc(),
                    QuickFillTemplate.history_count.desc(),
                    QuickFillTemplate.last_used_at.desc()
                )
            )
            if query:
                term = f"%{query.strip()}%"
                stmt = stmt.where(QuickFillTemplate.memo.ilike(term))

            if limit:
                stmt = stmt.limit(limit)

            return list(session.scalars(stmt).all())
        except Exception as exc:
            log_critical_application_error(
                f"Failed to rank QuickFill templates for {action_type}/{currency}: {exc}",
                metadata={"service": "TransactionService"}
            )
            raise RuntimeError("Failed to rank QuickFill templates due to unexpected error.") from exc
        finally:
            if should_close and session is not None:
                session.close()

    def scan_duplicate_candidates(  # noqa: C901
        self,
        *,
        account_id: str,
        scope: str = "account",
        limit: int = 25
    ) -> list[DuplicateCandidate]:
        """Scan recent transactions and persist candidates for manual review (account scope only)."""
        if scope not in {"account", "account_group"}:
            raise ValueError("scope must be either 'account' or 'account_group'.")

        if scope == "account_group":
            raise NotImplementedError("Account group duplicate scanning is not supported yet.")

        if scope == "account" and not account_id:
            raise ValueError("account_id is required for account-scoped duplicate scans.")

        if not self._use_db:
            raise RuntimeError("Duplicate scanning requires an active database session.")

        if limit <= 0:
            limit = 25

        session, should_close = self._acquire_session()
        try:
            txn_query = (
                select(Transaction)
                .where(
                    (Transaction.debit_account_id == account_id) |
                    (Transaction.credit_account_id == account_id)
                )
                .order_by(Transaction.effective_date.desc())
                .limit(DUPLICATE_SCAN_LIMIT)
            )
            transactions = list(session.scalars(txn_query).all())

            groups: dict[tuple[Decimal, date, str], list[Transaction]] = {}
            for txn in transactions:
                txn_date = txn.effective_date.date()
                description = (txn.description or txn.notes or "").strip()
                normalized_description = description[:255]
                key = (txn.amount, txn_date, normalized_description)
                groups.setdefault(key, []).append(txn)

            candidates: list[DuplicateCandidate] = []
            for (amount, txn_date, normalized_description), matches in groups.items():
                if len(matches) < 2:
                    continue

                matches.sort(key=lambda t: t.effective_date, reverse=True)
                txn_ids = [t.id for t in matches]
                confidence = min(Decimal("1.0"), Decimal(len(matches)) / Decimal("5.0"))

                existing = session.scalars(
                    select(DuplicateCandidate)
                    .where(
                        DuplicateCandidate.account_id == account_id,
                        DuplicateCandidate.scope == scope,
                        DuplicateCandidate.amount == amount,
                        DuplicateCandidate.date == txn_date,
                        DuplicateCandidate.description == normalized_description
                    )
                ).one_or_none()

                if existing:
                    existing.matching_transaction_ids = txn_ids
                    existing.confidence = confidence
                    existing.touch()
                    candidate = existing
                else:
                    candidate = DuplicateCandidate(
                        account_id=account_id,
                        scope=scope,
                        matching_transaction_ids=txn_ids,
                        amount=amount,
                        date=txn_date,
                        description=normalized_description or None,
                        confidence=confidence,
                        recommended_action="merge",
                        status="review"
                    )
                    session.add(candidate)

                candidates.append(candidate)

            session.flush()

            result_stmt = (
                select(DuplicateCandidate)
                .where(
                    DuplicateCandidate.account_id == account_id,
                    DuplicateCandidate.scope == scope
                )
                .order_by(DuplicateCandidate.confidence.desc(), DuplicateCandidate.updated_at.desc())
                .limit(limit)
            )
            return list(session.scalars(result_stmt).all())
        except Exception as exc:
            log_critical_application_error(
                f"Failed to scan duplicate candidates for account {account_id}: {exc}",
                metadata={"service": "TransactionService"}
            )
            raise RuntimeError("Failed to scan duplicate candidates due to unexpected error.") from exc
        finally:
            if should_close and session is not None:
                session.close()

    def validate_merge_depth(
        self,
        source_account_id: str,
        target_account_id: str
    ) -> tuple[bool, str | None]:
        """Ensure moving the source subtree under the target respects hierarchy depth limits."""
        if not self._use_db:
            raise RuntimeError("Account merge validation requires a database session.")

        session, should_close = self._acquire_session()
        try:
            depth_map = self._account_depth_map(session)
            source_depth = depth_map.get(source_account_id)
            target_depth = depth_map.get(target_account_id)

            if source_depth is None or target_depth is None:
                raise ValueError("Source or target account not found.")

            descendant_ids = self._collect_descendant_ids(session, source_account_id)
            max_descendant_depth = max((depth_map.get(acc_id, source_depth) for acc_id in descendant_ids), default=source_depth)
            delta = max_descendant_depth - source_depth
            new_depth = target_depth + 1 + delta

            if new_depth > MAX_HIERARCHY_DEPTH:
                message = (
                    f"Merge would place the deepest descendant at depth {new_depth}, "
                    f"exceeding the allowed limit of {MAX_HIERARCHY_DEPTH}."
                )
                return False, message

            return True, None
        except (ValueError, RuntimeError):
            raise
        except Exception as exc:
            log_critical_application_error(
                f"Failed to validate merge depth between {source_account_id} and {target_account_id}: {exc}",
                metadata={"service": "TransactionService"}
            )
            raise RuntimeError("Failed to validate merge depth due to unexpected error.") from exc
        finally:
            if should_close and session is not None:
                session.close()

    @staticmethod
    def _account_depth_map(session: Session) -> dict[str, int]:
        """Return a mapping of account IDs to their depth within the hierarchy."""
        hierarchy_cte = (
            select(
                Account.id.label("account_id"),
                literal(1).label("depth")
            )
            .where(Account.parent_account_id.is_(None))
            .cte(name="account_depth", recursive=True)
        )
        hierarchy_cte = hierarchy_cte.union_all(
            select(
                Account.id,
                (hierarchy_cte.c.depth + 1).label("depth")
            )
            .where(Account.parent_account_id == hierarchy_cte.c.account_id)
        )
        rows = session.execute(
            select(hierarchy_cte.c.account_id, hierarchy_cte.c.depth)
        ).all()
        return {row.account_id: row.depth for row in rows}

    @staticmethod
    def _collect_descendant_ids(session: Session, root_account_id: str) -> set[str]:
        """Return all account IDs in the subtree rooted at the provided account."""
        descendant_cte = (
            select(Account.id)
            .where(Account.id == root_account_id)
            .cte(name="merge_descendants", recursive=True)
        )
        descendant_cte = descendant_cte.union_all(
            select(Account.id)
            .where(Account.parent_account_id == descendant_cte.c.id)
        )
        rows = session.scalars(select(descendant_cte.c.id)).all()
        return set(rows)
