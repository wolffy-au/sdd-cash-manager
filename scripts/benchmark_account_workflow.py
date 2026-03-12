"""Simple benchmark for the Account Management service workflows."""

from __future__ import annotations

from datetime import datetime
from statistics import mean
from time import perf_counter
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sdd_cash_manager.models.base import Base
from sdd_cash_manager.services.account_service import AccountService
from sdd_cash_manager.services.transaction_service import TransactionService

ENGINE = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)


def run_benchmarks(account_count: int = 100) -> None:
    """Run benchmark scenarios and print average timings."""
    Base.metadata.drop_all(bind=ENGINE)
    Base.metadata.create_all(bind=ENGINE)
    service = AccountService(session_factory=lambda: SessionLocal())
    transaction_service = TransactionService()
    transaction_service.set_account_service(service)

    creation_times: list[float] = []
    balance_adjustments: list[float] = []
    created_ids: list[str] = []

    for i in range(account_count):
        name = f"benchmark-account-{i}-{uuid4()}"
        start = perf_counter()
        account = service.create_account(
            name=name,
            currency="USD",
            accounting_category="ASSET",
            available_balance=1000 + i,
            banking_product_type="BANK",
            notes="Benchmark account",
        )
        creation_times.append(perf_counter() - start)
        created_ids.append(account.id)

    adjustment_target = 1500.0
    for account_id in created_ids[-5:]:
        start = perf_counter()
        transaction_service.perform_balance_adjustment(
            account_id=account_id,
            target_balance=adjustment_target,
            adjustment_date=datetime.utcnow(),
            description="Benchmark adjustment",
            action_type="ADJUSTMENT",
            notes="Benchmark",
        )
        balance_adjustments.append(perf_counter() - start)

    query_start = perf_counter()
    service.get_all_accounts(search_term="benchmark", hidden=False, placeholder=False)
    query_duration = perf_counter() - query_start

    print("--- Benchmark Summary ---")
    print(f"Average account creation: {mean(creation_times):.6f}s")
    print(f"Average balance adjustment: {mean(balance_adjustments):.6f}s")
    print(f"Hierarchy query duration: {query_duration:.6f}s")


if __name__ == "__main__":
    run_benchmarks()
