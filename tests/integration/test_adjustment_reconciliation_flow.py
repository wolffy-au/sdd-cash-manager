import os
import uuid
from decimal import Decimal
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sdd_cash_manager.api.accounts import router as accounts_router
from sdd_cash_manager.api.v1.endpoints.adjustment import router as adjustment_router
from sdd_cash_manager.api.v1.endpoints.reconciliation import router as reconciliation_router
from sdd_cash_manager.database import get_db
from sdd_cash_manager.lib.auth import Role, create_access_token
from sdd_cash_manager.models.adjustment import AdjustmentTransaction, ManualBalanceAdjustment
from sdd_cash_manager.models.base import Base
from sdd_cash_manager.services.account_service import AccountService


@pytest.fixture(scope="function")
def override_get_db() -> Generator[Session, None, None]:
    db_path = f"./test_adjustment_flow_{uuid.uuid4().hex}.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.fixture(scope="function")
def adjustment_client(override_get_db: Session) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(accounts_router)
    app.include_router(adjustment_router)
    app.include_router(reconciliation_router)
    app.dependency_overrides[get_db] = lambda: override_get_db

    token = create_access_token(subject="integration-user", roles=[Role.OPERATOR])
    with TestClient(app) as client:
        client.headers.update({"Authorization": f"Bearer {token}"})
        yield client


@pytest.fixture(scope="function")
def seeded_account(override_get_db: Session) -> str:
    service = AccountService(override_get_db)
    account = service.create_account(
        name="Reconciliation Flow Account",
        currency="USD",
        accounting_category="ASSET",
        available_balance=Decimal("1000.00"),
    )
    return account.id


def test_adjustment_creates_reconciliation_entry(adjustment_client: TestClient, override_get_db: Session, seeded_account: str) -> None:
    payload = {
        "target_balance": "1200.00",
        "effective_date": "2026-04-01",
        "submitted_by_user_id": str(uuid.uuid4()),
    }

    response = adjustment_client.post(f"/accounts/{seeded_account}/adjust-balance", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["created_transaction_id"]

    manual_adjustments = (
        override_get_db.query(ManualBalanceAdjustment)
        .filter(ManualBalanceAdjustment.account_id == seeded_account)
        .all()
    )
    assert len(manual_adjustments) == 1
    manual_adjustment = manual_adjustments[0]
    assert manual_adjustment.status == "COMPLETED"
    assert manual_adjustment.created_transaction_id is not None

    transactions = (
        override_get_db.query(AdjustmentTransaction)
        .filter(AdjustmentTransaction.account_id == seeded_account)
        .all()
    )
    assert len(transactions) == 1

    recon_response = adjustment_client.get(f"/accounts/{seeded_account}/reconciliation")
    assert recon_response.status_code == 200
    recon_data = recon_response.json()
    assert len(recon_data) == 1
    entry = recon_data[0]
    assert entry["is_adjustment"] is True
    assert entry["reconciled_status"] == "PENDING_RECONCILIATION"
    transaction_amount = str(transactions[0].amount)
    assert entry["amount"] == transaction_amount


def test_zero_difference_adjustment_tracks_manual_entry(adjustment_client: TestClient, override_get_db: Session, seeded_account: str) -> None:
    payload = {
        "target_balance": "0.00",
        "effective_date": "2026-03-15",
        "submitted_by_user_id": str(uuid.uuid4()),
    }

    response = adjustment_client.post(f"/accounts/{seeded_account}/adjust-balance", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ZERO_DIFFERENCE"
    assert data["created_transaction_id"] is None

    manual_adjustment = (
        override_get_db.query(ManualBalanceAdjustment)
        .filter(ManualBalanceAdjustment.account_id == seeded_account)
        .one()
    )
    assert manual_adjustment.status == "ZERO_DIFFERENCE"
    assert manual_adjustment.created_transaction_id is None

    transaction_count = override_get_db.query(AdjustmentTransaction).count()
    assert transaction_count == 0

    recon_response = adjustment_client.get(f"/accounts/{seeded_account}/reconciliation")
    assert recon_response.status_code == 200
    recon_entries = recon_response.json()
    assert len(recon_entries) == 1
    entry = recon_entries[0]
    assert entry["reconciled_status"] == "ZERO_DIFFERENCE"
    assert entry["amount"] == "0.00"
