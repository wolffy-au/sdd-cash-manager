"""State management for application entities and unsaved changes tracking.

This module provides state management infrastructure for Account, Transaction, and Entry
entities, including lifecycle management, state transitions, and tracking of unsaved changes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class AccountLifecycleState(str, Enum):
    """Lifecycle states for Account entities."""

    DRAFT = "draft"  # Account created but not yet persisted
    ACTIVE = "active"  # Account is operational
    ARCHIVED = "archived"  # Account is archived and no longer active
    PENDING_ADJUSTMENT = "pending_adjustment"  # Account has pending balance adjustments
    CANCELLED = "cancelled"  # Account creation cancelled or removed before activation
    CLOSED = "closed"  # Account is closed


class TransactionLifecycleState(str, Enum):
    """Lifecycle states for Transaction entities."""

    DRAFT = "draft"  # Transaction created but not yet persisted
    PENDING = "pending"  # Transaction is pending processing
    POSTED = "posted"  # Transaction has been posted to accounts
    REVERSED = "reversed"  # Transaction has been reversed
    CANCELLED = "cancelled"  # Transaction has been cancelled


class EntryLifecycleState(str, Enum):
    """Lifecycle states for Entry entities."""

    DRAFT = "draft"  # Entry created but not yet persisted
    PENDING = "pending"  # Entry is pending posting
    POSTED = "posted"  # Entry has been posted
    REVERSED = "reversed"  # Entry has been reversed
    CANCELLED = "cancelled"  # Entry creation cancelled or skipped


@dataclass
class EntityState:
    """Tracks the state of an entity including lifecycle state and unsaved changes."""

    entity_id: str
    entity_type: str  # "Account", "Transaction", or "Entry"
    lifecycle_state: str  # Current lifecycle state
    original_values: dict[str, Any] = field(default_factory=dict)
    current_values: dict[str, Any] = field(default_factory=dict)
    has_unsaved_changes: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def mark_dirty(self, field_name: str, new_value: Any) -> None:
        """Mark a field as modified and track the change.

        Args:
            field_name: Name of the field that was modified
            new_value: New value of the field

        Raises:
            ValueError: If the field is not in the original values
        """
        if field_name not in self.original_values:
            raise ValueError(
                f"Field '{field_name}' is not tracked for entity '{self.entity_id}'"
            )

        self.current_values[field_name] = new_value
        self.has_unsaved_changes = True
        self.updated_at = datetime.now(timezone.utc)

    def get_changes(self) -> dict[str, tuple[Any, Any]]:
        """Get all unsaved changes as a dict of field_name: (old_value, new_value).

        Returns:
            Dictionary mapping field names to tuples of (original_value, current_value)
        """
        changes = {}
        for field_name in self.original_values:
            original = self.original_values[field_name]
            current = self.current_values.get(field_name, original)
            if original != current:
                changes[field_name] = (original, current)
        return changes

    def clear_changes(self) -> None:
        """Clear unsaved changes after successful persistence."""
        self.original_values = self.current_values.copy()
        self.current_values = {}
        self.has_unsaved_changes = False
        self.updated_at = datetime.now(timezone.utc)

    def discard_changes(self) -> None:
        """Discard all unsaved changes and revert to original values."""
        self.current_values = {}
        self.has_unsaved_changes = False
        self.updated_at = datetime.now(timezone.utc)


class StateTransitionValidator:
    """Validates state transitions for entities according to business rules."""

    # Define valid state transitions
    ACCOUNT_TRANSITIONS = {
        AccountLifecycleState.DRAFT: [
            AccountLifecycleState.ACTIVE,
            AccountLifecycleState.CANCELLED,
        ],
        AccountLifecycleState.ACTIVE: [
            AccountLifecycleState.ARCHIVED,
            AccountLifecycleState.PENDING_ADJUSTMENT,
            AccountLifecycleState.CLOSED,
        ],
        AccountLifecycleState.PENDING_ADJUSTMENT: [
            AccountLifecycleState.ACTIVE,
            AccountLifecycleState.ARCHIVED,
        ],
        AccountLifecycleState.ARCHIVED: [AccountLifecycleState.ACTIVE],
        AccountLifecycleState.CLOSED: [],  # Terminal state
    }

    TRANSACTION_TRANSITIONS = {
        TransactionLifecycleState.DRAFT: [
            TransactionLifecycleState.PENDING,
            TransactionLifecycleState.CANCELLED,
        ],
        TransactionLifecycleState.PENDING: [
            TransactionLifecycleState.POSTED,
            TransactionLifecycleState.CANCELLED,
        ],
        TransactionLifecycleState.POSTED: [
            TransactionLifecycleState.REVERSED,
        ],
        TransactionLifecycleState.REVERSED: [TransactionLifecycleState.POSTED],
        TransactionLifecycleState.CANCELLED: [],  # Terminal state
    }

    ENTRY_TRANSITIONS = {
        EntryLifecycleState.DRAFT: [
            EntryLifecycleState.PENDING,
            EntryLifecycleState.CANCELLED,
        ],
        EntryLifecycleState.PENDING: [
            EntryLifecycleState.POSTED,
        ],
        EntryLifecycleState.POSTED: [
            EntryLifecycleState.REVERSED,
        ],
        EntryLifecycleState.REVERSED: [EntryLifecycleState.POSTED],
    }

    @classmethod
    def validate_account_transition(
        cls, current_state: str, target_state: str
    ) -> bool:
        """Validate if an account can transition from current to target state.

        Args:
            current_state: Current lifecycle state
            target_state: Target lifecycle state to transition to

        Returns:
            True if transition is valid, False otherwise

        Raises:
            ValueError: If states are invalid
        """
        try:
            current = AccountLifecycleState(current_state)
            target = AccountLifecycleState(target_state)
        except ValueError as e:
            raise ValueError(f"Invalid account state: {e}") from e

        if current not in cls.ACCOUNT_TRANSITIONS:
            raise ValueError(f"Unknown account state: {current}")

        return target in cls.ACCOUNT_TRANSITIONS[current]

    @classmethod
    def validate_transaction_transition(
        cls, current_state: str, target_state: str
    ) -> bool:
        """Validate if a transaction can transition from current to target state.

        Args:
            current_state: Current lifecycle state
            target_state: Target lifecycle state to transition to

        Returns:
            True if transition is valid, False otherwise

        Raises:
            ValueError: If states are invalid
        """
        try:
            current = TransactionLifecycleState(current_state)
            target = TransactionLifecycleState(target_state)
        except ValueError as e:
            raise ValueError(f"Invalid transaction state: {e}") from e

        if current not in cls.TRANSACTION_TRANSITIONS:
            raise ValueError(f"Unknown transaction state: {current}")

        return target in cls.TRANSACTION_TRANSITIONS[current]

    @classmethod
    def validate_entry_transition(
        cls, current_state: str, target_state: str
    ) -> bool:
        """Validate if an entry can transition from current to target state.

        Args:
            current_state: Current lifecycle state
            target_state: Target lifecycle state to transition to

        Returns:
            True if transition is valid, False otherwise

        Raises:
            ValueError: If states are invalid
        """
        try:
            current = EntryLifecycleState(current_state)
            target = EntryLifecycleState(target_state)
        except ValueError as e:
            raise ValueError(f"Invalid entry state: {e}") from e

        if current not in cls.ENTRY_TRANSITIONS:
            raise ValueError(f"Unknown entry state: {current}")

        return target in cls.ENTRY_TRANSITIONS[current]


class StateManager:
    """Manages entity state and lifecycle transitions."""

    def __init__(self) -> None:
        """Initialize the state manager with an empty state store."""
        self._state_store: dict[str, EntityState] = {}
        self._transition_validator = StateTransitionValidator()

    def track_account(
        self,
        account_id: str,
        initial_values: dict[str, Any],
        lifecycle_state: str = AccountLifecycleState.DRAFT,
    ) -> EntityState:
        """Start tracking an account entity.

        Args:
            account_id: Unique identifier for the account
            initial_values: Dictionary of initial field values
            lifecycle_state: Initial lifecycle state for the account

        Returns:
            EntityState object for the account
        """
        state = EntityState(
            entity_id=account_id,
            entity_type="Account",
            lifecycle_state=lifecycle_state,
            original_values=initial_values.copy(),
            current_values={},
        )
        self._state_store[account_id] = state
        return state

    def track_transaction(
        self,
        transaction_id: str,
        initial_values: dict[str, Any],
        lifecycle_state: str = TransactionLifecycleState.DRAFT,
    ) -> EntityState:
        """Start tracking a transaction entity.

        Args:
            transaction_id: Unique identifier for the transaction
            initial_values: Dictionary of initial field values
            lifecycle_state: Initial lifecycle state for the transaction

        Returns:
            EntityState object for the transaction
        """
        state = EntityState(
            entity_id=transaction_id,
            entity_type="Transaction",
            lifecycle_state=lifecycle_state,
            original_values=initial_values.copy(),
            current_values={},
        )
        self._state_store[transaction_id] = state
        return state

    def track_entry(
        self,
        entry_id: str,
        initial_values: dict[str, Any],
        lifecycle_state: str = EntryLifecycleState.DRAFT,
    ) -> EntityState:
        """Start tracking an entry entity.

        Args:
            entry_id: Unique identifier for the entry
            initial_values: Dictionary of initial field values
            lifecycle_state: Initial lifecycle state for the entry

        Returns:
            EntityState object for the entry
        """
        state = EntityState(
            entity_id=entry_id,
            entity_type="Entry",
            lifecycle_state=lifecycle_state,
            original_values=initial_values.copy(),
            current_values={},
        )
        self._state_store[entry_id] = state
        return state

    def get_state(self, entity_id: str) -> Optional[EntityState]:
        """Retrieve the state of an entity.

        Args:
            entity_id: Unique identifier for the entity

        Returns:
            EntityState if found, None otherwise
        """
        return self._state_store.get(entity_id)

    def mark_dirty(self, entity_id: str, field_name: str, new_value: Any) -> None:
        """Mark a field as modified for an entity.

        Args:
            entity_id: Unique identifier for the entity
            field_name: Name of the field that was modified
            new_value: New value of the field

        Raises:
            ValueError: If entity is not being tracked
        """
        state = self.get_state(entity_id)
        if state is None:
            raise ValueError(f"Entity '{entity_id}' is not being tracked")
        state.mark_dirty(field_name, new_value)

    def transition_account_state(
        self, account_id: str, target_state: str
    ) -> bool:
        """Transition an account to a new lifecycle state.

        Args:
            account_id: Unique identifier for the account
            target_state: Target lifecycle state

        Returns:
            True if transition was successful

        Raises:
            ValueError: If entity not found or transition is invalid
        """
        state = self.get_state(account_id)
        if state is None:
            raise ValueError(f"Entity '{account_id}' is not being tracked")

        if not self._transition_validator.validate_account_transition(
            state.lifecycle_state, target_state
        ):
            raise ValueError(
                f"Cannot transition account from {state.lifecycle_state} to {target_state}"
            )

        state.lifecycle_state = target_state
        state.updated_at = datetime.now(timezone.utc)
        return True

    def transition_transaction_state(
        self, transaction_id: str, target_state: str
    ) -> bool:
        """Transition a transaction to a new lifecycle state.

        Args:
            transaction_id: Unique identifier for the transaction
            target_state: Target lifecycle state

        Returns:
            True if transition was successful

        Raises:
            ValueError: If entity not found or transition is invalid
        """
        state = self.get_state(transaction_id)
        if state is None:
            raise ValueError(f"Entity '{transaction_id}' is not being tracked")

        if not self._transition_validator.validate_transaction_transition(
            state.lifecycle_state, target_state
        ):
            raise ValueError(
                f"Cannot transition transaction from {state.lifecycle_state} to {target_state}"
            )

        state.lifecycle_state = target_state
        state.updated_at = datetime.now(timezone.utc)
        return True

    def transition_entry_state(
        self, entry_id: str, target_state: str
    ) -> bool:
        """Transition an entry to a new lifecycle state.

        Args:
            entry_id: Unique identifier for the entry
            target_state: Target lifecycle state

        Returns:
            True if transition was successful

        Raises:
            ValueError: If entity not found or transition is invalid
        """
        state = self.get_state(entry_id)
        if state is None:
            raise ValueError(f"Entity '{entry_id}' is not being tracked")

        if not self._transition_validator.validate_entry_transition(
            state.lifecycle_state, target_state
        ):
            raise ValueError(
                f"Cannot transition entry from {state.lifecycle_state} to {target_state}"
            )

        state.lifecycle_state = target_state
        state.updated_at = datetime.now(timezone.utc)
        return True

    def persist_changes(self, entity_id: str) -> None:
        """Mark changes as persisted for an entity.

        Args:
            entity_id: Unique identifier for the entity

        Raises:
            ValueError: If entity is not being tracked
        """
        state = self.get_state(entity_id)
        if state is None:
            raise ValueError(f"Entity '{entity_id}' is not being tracked")
        state.clear_changes()

    def discard_changes(self, entity_id: str) -> None:
        """Discard unsaved changes for an entity.

        Args:
            entity_id: Unique identifier for the entity

        Raises:
            ValueError: If entity is not being tracked
        """
        state = self.get_state(entity_id)
        if state is None:
            raise ValueError(f"Entity '{entity_id}' is not being tracked")
        state.discard_changes()

    def get_all_dirty_entities(self) -> list[EntityState]:
        """Get all entities with unsaved changes.

        Returns:
            List of EntityState objects with unsaved changes
        """
        return [
            state for state in self._state_store.values()
            if state.has_unsaved_changes
        ]

    def clear_all(self) -> None:
        """Clear all tracked state."""
        self._state_store.clear()
