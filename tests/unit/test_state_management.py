
import pytest

from sdd_cash_manager.lib.state_management import (
    AccountLifecycleState,
    EntryLifecycleState,
    StateManager,
    StateTransitionValidator,
    TransactionLifecycleState,
)


def test_track_account_and_mark_dirty():
    mgr = StateManager()
    account_id = "acct-1"
    initial = {"name": "Cash Account", "available_balance": 100.0}

    state = mgr.track_account(account_id, initial_values=initial)
    assert state.entity_id == account_id
    assert state.entity_type == "Account"
    assert state.lifecycle_state == AccountLifecycleState.DRAFT
    assert not state.has_unsaved_changes

    # Mark a tracked field as dirty
    mgr.mark_dirty(account_id, "available_balance", 150.0)
    s = mgr.get_state(account_id)
    assert s is not None and s.has_unsaved_changes
    changes = s.get_changes()
    assert "available_balance" in changes
    assert changes["available_balance"] == (100.0, 150.0)


def test_transition_account_valid_and_invalid():
    mgr = StateManager()
    account_id = "acct-2"
    initial = {"name": "Savings", "available_balance": 0.0}
    mgr.track_account(account_id, initial_values=initial, lifecycle_state=AccountLifecycleState.DRAFT)

    # Valid transition DRAFT -> ACTIVE
    assert mgr.transition_account_state(account_id, AccountLifecycleState.ACTIVE)
    st = mgr.get_state(account_id)
    assert st is not None
    assert st.lifecycle_state == AccountLifecycleState.ACTIVE

    # Invalid transition ACTIVE -> DRAFT should raise
    with pytest.raises(ValueError):
        mgr.transition_account_state(account_id, AccountLifecycleState.DRAFT)


def test_persist_and_discard_changes():
    mgr = StateManager()
    tx_id = "tx-1"
    initial = {"description": "Initial", "amount": 10.0}
    mgr.track_transaction(tx_id, initial_values=initial)

    mgr.mark_dirty(tx_id, "amount", 20.0)
    st = mgr.get_state(tx_id)
    assert st is not None
    assert st.has_unsaved_changes

    mgr.persist_changes(tx_id)
    st2 = mgr.get_state(tx_id)
    assert st2 is not None
    assert not st2.has_unsaved_changes
    # original_values should now reflect persisted current values
    assert st2.original_values["amount"] == 20.0

    # Mark dirty again and then discard
    mgr.mark_dirty(tx_id, "amount", 30.0)
    st3 = mgr.get_state(tx_id)
    assert st3 is not None and st3.has_unsaved_changes
    mgr.discard_changes(tx_id)
    st4 = mgr.get_state(tx_id)
    assert st4 is not None and not st4.has_unsaved_changes
    # value reverts to previously persisted value 20.0
    assert st4.original_values["amount"] == 20.0


def test_get_all_dirty_entities_and_errors():
    mgr = StateManager()
    mgr.track_account("a1", {"name": "A1", "available_balance": 0.0})
    mgr.track_account("a2", {"name": "A2", "available_balance": 0.0})
    mgr.track_transaction("t1", {"description": "t1", "amount": 1.0})

    mgr.mark_dirty("a1", "available_balance", 5.0)
    mgr.mark_dirty("t1", "amount", 2.0)

    dirty = mgr.get_all_dirty_entities()
    ids = {s.entity_id for s in dirty}
    assert ids == {"a1", "t1"}

    # Attempt to mark dirty on untracked entity
    with pytest.raises(ValueError):
        mgr.mark_dirty("unknown", "foo", "bar")

    # Attempt to mark a field not tracked
    with pytest.raises(ValueError):
        mgr.mark_dirty("a2", "nonexistent_field", 123)

    # Attempt transitions on unknown entities
    with pytest.raises(ValueError):
        mgr.transition_entry_state("no_entry", EntryLifecycleState.POSTED)


def test_validate_transition_invalid_states():
    with pytest.raises(ValueError):
        StateTransitionValidator.validate_account_transition("invalid", "active")
    with pytest.raises(ValueError):
        StateTransitionValidator.validate_transaction_transition("draft", "invalid")
    with pytest.raises(ValueError):
        StateTransitionValidator.validate_entry_transition("invalid", "posted")


def test_entry_and_transaction_transitions_and_clear_all():
    mgr = StateManager()
    # Track and transition entry
    e = mgr.track_entry("e1", {"amount": 10.0}, lifecycle_state=EntryLifecycleState.DRAFT)
    assert e.lifecycle_state == EntryLifecycleState.DRAFT
    assert mgr.transition_entry_state("e1", EntryLifecycleState.PENDING)
    st = mgr.get_state("e1")
    assert st is not None and st.lifecycle_state == EntryLifecycleState.PENDING
    # Invalid transition from PENDING -> DRAFT
    with pytest.raises(ValueError):
        mgr.transition_entry_state("e1", EntryLifecycleState.DRAFT)

    # Track transaction and valid/invalid transitions
    t = mgr.track_transaction("t1", {"amount": 5.0}, lifecycle_state=TransactionLifecycleState.DRAFT)
    assert t.lifecycle_state == TransactionLifecycleState.DRAFT
    assert mgr.transition_transaction_state("t1", TransactionLifecycleState.PENDING)
    stt = mgr.get_state("t1")
    assert stt is not None and stt.lifecycle_state == TransactionLifecycleState.PENDING
    with pytest.raises(ValueError):
        mgr.transition_transaction_state("t1", TransactionLifecycleState.DRAFT)

    # Mark dirty and clear all
    mgr.mark_dirty("e1", "amount", 20.0)
    dirty = mgr.get_all_dirty_entities()
    assert any(s.entity_id == "e1" for s in dirty)
    mgr.clear_all()
    assert mgr.get_all_dirty_entities() == []


def test_transition_untracked_entity_raises():
    mgr = StateManager()
    with pytest.raises(ValueError):
        mgr.transition_account_state("no_such", AccountLifecycleState.ACTIVE)
    with pytest.raises(ValueError):
        mgr.transition_transaction_state("no_such", TransactionLifecycleState.POSTED)
    with pytest.raises(ValueError):
        mgr.transition_entry_state("no_such", EntryLifecycleState.POSTED)


if __name__ == "__main__":
    # quick way to run tests locally
    import pytest

    pytest.main([__file__])
