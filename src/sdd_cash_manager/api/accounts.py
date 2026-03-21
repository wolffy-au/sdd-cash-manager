import re
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Annotated, TypedDict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, condecimal, constr, field_validator
from sqlalchemy.orm import Session

from sdd_cash_manager.database import get_db
from sdd_cash_manager.lib.auth import Role, TokenPayload, require_role
from sdd_cash_manager.lib.logging_config import get_logger
from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.account_merge_plan import AccountMergePlan
from sdd_cash_manager.models.duplicate_candidate import DuplicateCandidate
from sdd_cash_manager.models.quickfill_template import QuickFillTemplate
from sdd_cash_manager.models.transaction import Transaction
from sdd_cash_manager.schemas.account_schema import AccountResponse
from sdd_cash_manager.schemas.transaction_schema import (
    AccountMergePlanRequest,
    AccountMergePlanResponse,
    ActionField,
    BalanceAdjustmentResponse,
    DuplicateCandidateResponse,
    DuplicateMergeRequest,
    DuplicateMergeResponse,
    QuickFillTemplateResponse,
    TransactionEntryResponse,
    TransactionRequest,
    TransactionResponse,
)
from sdd_cash_manager.services.account_service import AccountService
from sdd_cash_manager.services.transaction_service import TransactionService

ALLOWED_CURRENCIES = {
    "USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "NZD", "SGD", "CNY"
}
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1F\x7F]")
NAME_ALLOWED_PATTERN = re.compile(r"^[A-Za-z0-9\s\.\,\-\_\(\)\&']+$")
ACCOUNT_NUMBER_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
MAX_SEARCH_TERM_LENGTH = 100
ACCOUNT_NOT_FOUND_DETAIL = "Account not found"

NameField = Annotated[str, constr(strip_whitespace=True, min_length=1, max_length=100)]
CurrencyField = Annotated[str, constr(min_length=3, max_length=3)]
AccountNumberField = Annotated[str, constr(strip_whitespace=True, max_length=50)]
BalanceField = Annotated[Decimal, condecimal(max_digits=18, decimal_places=2, ge=Decimal("0"))]
NotesField = Annotated[str, constr(strip_whitespace=True, max_length=500)]
DescriptionField = Annotated[str, constr(strip_whitespace=True, min_length=1, max_length=255)]

OptionalNameField = NameField | None
OptionalCurrencyField = CurrencyField | None
OptionalAccountNumberField = AccountNumberField | None
OptionalBalanceField = BalanceField | None
OptionalNotesField = NotesField | None


class _AccountCreationPayload(TypedDict):
    name: str
    currency: str
    accounting_category: str
    account_number: str | None
    banking_product_type: str
    available_balance: Decimal
    credit_limit: Decimal | None
    notes: str | None
    parent_account_id: str | None
    hidden: bool
    placeholder: bool
    id: str | None

def _validate_name_value(value: str) -> str:
    """Validate that the provided account name contains only supported characters.

    Args:
        value: The raw account name from the request payload.

    Returns:
        The validated account name when validation passes.

    Raises:
        ValueError: When the name includes unsupported characters or invalid symbols.
    """
    _assert_no_control_chars(value, "account name")
    if not NAME_ALLOWED_PATTERN.match(value):
        raise ValueError("account name contains unsupported characters")
    if any(ch in value for ch in "<>;"):
        raise ValueError("account name contains invalid characters")
    return value

def _validate_currency_value(value: str) -> str:
    """Validate that the currency is one of the allowed ISO 4217 codes.

    Args:
        value: The currency code provided in the request payload.

    Returns:
        The provided currency when it is allowed.

    Raises:
        ValueError: When the currency code is not in the allowed set.
    """
    if value not in ALLOWED_CURRENCIES:
        raise ValueError("unsupported currency")
    return value

def _validate_text_field_no_special_chars(value: str, field_name: str, invalid_message: str) -> str:
    """Ensure the specified text field does not contain control or disallowed characters.

    Args:
        value: The text value provided in the payload.
        field_name: The human-readable field name used in error messages.
        invalid_message: The message to raise when invalid characters are found.

    Returns:
        The validated text value when no disallowed characters remain.

    Raises:
        ValueError: When the text contains control characters or forbidden symbols.
    """
    _assert_no_control_chars(value, field_name)
    if any(ch in value for ch in "<>;"):
        raise ValueError(invalid_message)
    return value


def _validate_account_number_value(value: str | None) -> str | None:
    """Ensure account numbers are alphanumeric with dashes only."""
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        raise ValueError("account number cannot be empty.")
    if not ACCOUNT_NUMBER_PATTERN.fullmatch(normalized):
        raise ValueError("account number contains invalid characters.")
    return normalized

class AccountingCategory(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"

class BankingProductType(str, Enum):
    # Primary canonical product types used internally
    BANK = "BANK"
    CREDIT_CARD = "CREDIT_CARD"
    LOAN = "LOAN"
    CASH = "CASH"
    INVESTMENT = "INVESTMENT"
    OTHER = "OTHER"
    # Legacy / alternate names accepted by the public API and mapped to canonical values
    CHECKING = "BANK"  # Accept 'CHECKING' from older clients and treat as 'BANK'

class ActionType(str, Enum):
    ADJUSTMENT = "ADJUSTMENT"
    CORRECTION = "CORRECTION"
    REVERSAL = "REVERSAL"

def _assert_no_control_chars(value: str, field_name: str) -> str:
    """Assert that the given value contains no Unicode control characters.

    Args:
        value: The string value to inspect.
        field_name: The name of the field used for contextual error reporting.

    Returns:
        The original value if it does not contain control characters.

    Raises:
        ValueError: When the value contains control characters.
    """
    if CONTROL_CHAR_PATTERN.search(value):
        raise ValueError(f"{field_name} contains invalid characters")
    return value

class AccountCreatePayload(BaseModel):
    name: NameField
    currency: CurrencyField
    accounting_category: AccountingCategory
    # Accept strings for legacy client values (e.g., "CHECKING") and validate later
    banking_product_type: str
    account_number: AccountNumberField | None = None
    credit_limit: BalanceField | None = None
    notes: NotesField | None = None
    parent_account_id: UUID | None = None
    id: str | None = None
    hidden: bool = False
    placeholder: bool = False
    available_balance: BalanceField = Decimal("0.0")

    @field_validator("name")
    def _validate_name(cls, value: str) -> str:
        return _validate_name_value(value)

    @field_validator("currency")
    def _validate_currency(cls, value: str) -> str:
        return _validate_currency_value(value)

    @field_validator("notes")
    def _validate_notes(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_text_field_no_special_chars(value, "notes", "notes contain invalid characters")

    @field_validator("account_number")
    def _validate_account_number(cls, value: str | None) -> str | None:
        return _validate_account_number_value(value)

class AccountUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: NameField | None = None
    currency: CurrencyField | None = None
    accounting_category: AccountingCategory | None = None
    banking_product_type: str | None = None
    account_number: AccountNumberField | None = None
    available_balance: BalanceField | None = None
    credit_limit: BalanceField | None = None
    notes: NotesField | None = None
    parent_account_id: UUID | None = None
    hidden: bool | None = None
    placeholder: bool | None = None

    @field_validator("account_number")
    def _validate_account_number(cls, value: str | None) -> str | None:
        return _validate_account_number_value(value)



class BalanceAdjustmentPayload(BaseModel):
    target_balance: BalanceField
    adjustment_date: date
    description: DescriptionField
    action_type: ActionType
    notes: NotesField | None = None

    @field_validator("description")
    def _validate_description(cls, value: str) -> str:
        return _validate_text_field_no_special_chars(value, "description", "description contains invalid characters")

    @field_validator("notes")
    def _validate_notes(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_text_field_no_special_chars(value, "adjustment notes", "notes contain invalid characters")

def _sanitize_search_term(search_term: str | None) -> str | None:
    """Trim and validate an optional search term for account queries.

    Args:
        search_term: The raw search term provided by the client.

    Returns:
        The sanitized search term or None when no term was provided.

    Raises:
        HTTPException: When the term exceeds length limits or contains control characters.
    """
    if search_term is None:
        return None
    trimmed = search_term.strip()
    if len(trimmed) > MAX_SEARCH_TERM_LENGTH:
        raise HTTPException(status_code=400, detail="Search term exceeds maximum allowed length.")
    if CONTROL_CHAR_PATTERN.search(trimmed):
        raise HTTPException(status_code=400, detail="Search term contains invalid characters.")
    return trimmed

def _ensure_parent_account_exists(account_service: AccountService, parent_account_id: UUID | None) -> str | None:
    """Verify that a parent account exists when an ID is provided.

    Args:
        account_service: The service managing account data.
        parent_account_id: The UUID of the parent account to validate.

    Returns:
        The parent account ID as a string when the parent exists, otherwise None.

    Raises:
        HTTPException: When the provided parent account ID cannot be found.
    """
    if parent_account_id is None:
        return None
    parent = account_service.get_account(str(parent_account_id))
    if parent is None:
        raise HTTPException(status_code=400, detail="Parent account not found.")
    return str(parent_account_id)

def _quantize_amount(value: Decimal) -> Decimal:
    """Quantize amounts to two decimal places for API consistency.

    Args:
        value: The raw Decimal amount provided in the payload.

    Returns:
        The amount quantized to two decimal places.
    """
    return value.quantize(Decimal("0.01"))


def _normalize_banking_product_type(value: str | Enum) -> str:
    """Return the string representation of banking product type payloads."""
    if isinstance(value, Enum):
        return str(value.value)
    return value


def _normalize_optional_balance(value: Decimal | None) -> Decimal | None:
    """Quantize optional balance fields when provided."""
    if value is None:
        return None
    return _quantize_amount(value)


def _build_account_creation_kwargs(
    account_data: AccountCreatePayload,
    parent_account_id: str | None,
) -> _AccountCreationPayload:
    """Assemble consistent kwargs when creating a new account."""
    return {
        "name": account_data.name,
        "currency": account_data.currency,
        "accounting_category": account_data.accounting_category.value,
        "account_number": account_data.account_number,
        "banking_product_type": _normalize_banking_product_type(account_data.banking_product_type),
        "available_balance": _quantize_amount(account_data.available_balance),
        "credit_limit": _normalize_optional_balance(account_data.credit_limit),
        "notes": account_data.notes,
        "parent_account_id": parent_account_id,
        "hidden": account_data.hidden,
        "placeholder": account_data.placeholder,
        "id": str(account_data.id) if account_data.id is not None else None,
    }


def _account_response_from_model(account: Account, account_service: AccountService) -> AccountResponse:
    """Return an AccountResponse while decrypting sensitive fields."""
    payload = account.__dict__.copy()
    decrypt_notes = getattr(account_service, "decrypt_notes", lambda value: value)
    payload["notes"] = decrypt_notes(getattr(account, "notes", None))

    available_balance = getattr(account, "available_balance", None)
    if isinstance(available_balance, Decimal):
        payload["available_balance"] = float(available_balance)

    credit_limit = getattr(account, "credit_limit", None)
    if isinstance(credit_limit, Decimal):
        payload["credit_limit"] = float(credit_limit)

    hierarchy_balance = account_service.get_account_hierarchy_balance(account.id)
    payload["hierarchy_balance"] = float(hierarchy_balance)
    return AccountResponse(**payload)


def _transaction_response_from_model(transaction: Transaction) -> TransactionResponse:
    """Build a TransactionResponse that includes all ledger entries."""
    entries = [
        TransactionEntryResponse(
            entry_id=entry.id,
            account_id=entry.account_id,
            debit_amount=entry.debit_amount,
            credit_amount=entry.credit_amount,
            notes=entry.notes,
        )
        for entry in transaction.entries
    ]
    return TransactionResponse(
        transaction_id=transaction.id,
        effective_date=transaction.effective_date,
        booking_date=transaction.booking_date,
        description=transaction.description,
        action_type=transaction.action_type,
        amount=transaction.amount,
        debit_account_id=transaction.debit_account_id,
        credit_account_id=transaction.credit_account_id,
        processing_status=str(transaction.processing_status),
        reconciliation_status=str(transaction.reconciliation_status),
        notes=transaction.notes,
        entries=entries,
    )


def _quickfill_template_response_from_model(template: QuickFillTemplate) -> QuickFillTemplateResponse:
    """Serialize a QuickFill template for API responses."""
    return QuickFillTemplateResponse(
        id=template.id,
        action=template.action,
        currency=template.currency,
        transfer_from_account_id=template.transfer_from_account_id,
        transfer_to_account_id=template.transfer_to_account_id,
        amount=template.amount,
        memo=template.memo,
        confidence_score=template.confidence_score,
        history_count=template.history_count,
        last_used_at=template.last_used_at,
        is_approved=template.is_approved,
        approved_at=template.approved_at,
    )

def _create_transaction_response_from_payload(
    payload: TransactionRequest,
    transaction_service: TransactionService,
    current_user: TokenPayload,
) -> TransactionResponse:
    """Persist a transaction request and return the serialized response."""
    description = payload.description or payload.action
    description = _validate_text_field_no_special_chars(description, "description", "description contains invalid characters")
    memo = payload.memo
    if memo is not None:
        memo = _validate_text_field_no_special_chars(memo, "memo", "memo contains invalid characters")

    effective_date = datetime.combine(payload.date or date.today(), datetime.min.time(), tzinfo=timezone.utc)
    booking_date = datetime.now(timezone.utc)

    transaction = transaction_service.create_transaction(
        effective_date=effective_date,
        booking_date=booking_date,
        description=description,
        amount=payload.amount,
        debit_account_id=str(payload.transfer_from),
        credit_account_id=str(payload.transfer_to),
        action_type=payload.action,
        notes=memo,
        currency=payload.currency,
    )
    logger.info(
        "Transaction created txn=%s from=%s to=%s user=%s",
        transaction.id,
        transaction.debit_account_id,
        transaction.credit_account_id,
        current_user.subject,
    )
    return _transaction_response_from_model(transaction)


def _handle_transaction_request(
    payload: TransactionRequest,
    transaction_service: TransactionService,
    current_user: TokenPayload,
) -> TransactionResponse:
    """Wrap the transaction creation flow with HTTP-friendly error handling."""
    try:
        return _create_transaction_response_from_payload(payload, transaction_service, current_user)
    except ValueError as exc:
        logger.warning("Rejected transaction request: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Transaction creation failed for user=%s", current_user.subject)
        raise HTTPException(status_code=500, detail="Unable to create transaction at this time.") from exc


def _resolve_current_user(user: TokenPayload | object) -> TokenPayload:
    """Return the provided TokenPayload or fall back to a system user for direct calls."""
    if isinstance(user, TokenPayload):
        return user
    return TokenPayload(subject="system", roles=[Role.ADMIN])

# Helper functions for dependency implementation
# These are NOT the FastAPI providers themselves, but the logic they use.
def _get_account_service_impl(db: Session) -> AccountService:
    """Instantiate the account service using the provided database session.

    Args:
        db: The current SQLAlchemy session.

    Returns:
        An AccountService bound to the provided session.
    """
    return AccountService(db)

# Module-level dependency instances (these ARE the FastAPI providers) - Defined early for use in other _get_..._impl functions
db_dependency = Depends(get_db)
account_service_dependency = Depends(lambda db=db_dependency: _get_account_service_impl(db=db))


def _get_transaction_service_impl(db: Session = db_dependency, account_service: AccountService = account_service_dependency) -> TransactionService:
    """Instantiate the transaction service and attach the account service.

    Args:
        db: The current SQLAlchemy session.
        account_service: The account service used to load account data.

    Returns:
        A TransactionService configured with the account service.
    """
    ts = TransactionService(db_session=db) # Pass db_session here
    ts.set_account_service(account_service)
    return ts

transaction_service_dependency = Depends(_get_transaction_service_impl)
_operator_dependency = Depends(require_role(Role.OPERATOR))
_viewer_dependency = Depends(require_role(Role.VIEWER))
_admin_dependency = Depends(require_role(Role.ADMIN))
logger = get_logger(__name__)

def _duplicate_candidate_to_response(candidate: DuplicateCandidate) -> DuplicateCandidateResponse:
    return DuplicateCandidateResponse(
        candidate_id=candidate.id,
        account_id=candidate.account_id,
        scope=candidate.scope,
        matching_transaction_ids=candidate.matching_transaction_ids,
        amount=candidate.amount,
        date=candidate.date,
        description=candidate.description,
        confidence=candidate.confidence,
        status=candidate.status,
    )


def _duplicate_merge_response(
    candidate: DuplicateCandidate,
    canonical_id: str,
    removed_transaction_ids: list[str],
    before_balance: Decimal,
    after_balance: Decimal,
) -> DuplicateMergeResponse:
    return DuplicateMergeResponse(
        candidate_id=candidate.id,
        canonical_transaction_id=canonical_id,
        removed_transaction_ids=removed_transaction_ids,
        before_balance=before_balance,
        after_balance=after_balance,
        status=candidate.status,
    )


def _account_merge_plan_response(plan: AccountMergePlan) -> AccountMergePlanResponse:
    return AccountMergePlanResponse(
        plan_id=plan.plan_id,
        source_account_id=plan.source_account_id,
        target_account_id=plan.target_account_id,
        reparenting_map=plan.reparenting_map,
        affected_entries_count=plan.affected_entries_count,
        status=plan.status,
        depth_validation_error=plan.depth_validation_error,
        audit_notes=plan.audit_notes,
        initiated_by=plan.initiated_by,
        metadata=plan.plan_metadata,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        executed_at=plan.executed_at,
    )

# --- Helper Utilities for Filters ---
def _parse_bool_flag(value: str | None) -> bool | None:
    if value is None:
        return None
    return str(value).strip().lower() in ("1", "true", "yes")


def _resolve_visibility_filter(
    explicit_flag: bool | None,
    include_flag_value: str | None,
    default_value: bool,
) -> bool | None:
    if explicit_flag is not None:
        return explicit_flag
    if include_flag_value is None:
        return default_value
    include_flag = _parse_bool_flag(include_flag_value)
    return None if include_flag else False


def _apply_account_filters(
    accounts: list[Account],
    hidden_filter: bool | None,
    placeholder_filter: bool | None,
    search_term: str | None,
) -> list[Account]:
    filtered = accounts
    if hidden_filter is not None:
        filtered = [acc for acc in filtered if acc.hidden == hidden_filter]
    if placeholder_filter is not None:
        filtered = [acc for acc in filtered if acc.placeholder == placeholder_filter]
    if search_term:
        term = search_term.lower()
        filtered = [acc for acc in filtered if term in acc.name.lower()]
    return filtered

# --- API Router ---
router = APIRouter(prefix="/accounts", tags=["Accounts"])
transactions_router = APIRouter(tags=["Transactions"])
quickfill_router = APIRouter(prefix="/quickfill", tags=["QuickFill"])
quickfill_router = APIRouter(prefix="/quickfill", tags=["QuickFill"])

@router.get("/health", status_code=200, tags=["Monitoring"])
def health_check():
    """
    Health check endpoint to verify the API is running.
    Returns a simple 200 OK status.
    """
    print("Health check endpoint hit!") # Debug print
    return {"status": "ok"}


def _handle_request_validation_error(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )

_exception_handler = getattr(router, "add_exception_handler", None)
if _exception_handler is not None:  # pragma: no branch - runtime routers have the method
    _exception_handler(RequestValidationError, _handle_request_validation_error)

# --- Account Endpoints ---

@router.post(
    "/",
    status_code=201,
    responses={
        400: {"description": "Invalid account details or missing/invalid parent account reference."},
        500: {"description": "Unexpected error while creating the account."},
    },
)
def create_account(
    account_data: AccountCreatePayload,
    account_service: AccountService = account_service_dependency,
    _current_user: TokenPayload = _operator_dependency
) -> AccountResponse:
    """Create a new financial account.

    Args:
        account_data: The payload describing the account to create.
        account_service: The service responsible for account lifecycle management.

    Returns:
        An AccountResponse describing the newly created account.

    Raises:
        HTTPException: On validation errors (400), missing parent account, or unexpected failures (500).
    """
    current_user = _resolve_current_user(_current_user)
    logger.info(
        "Create account request: name=%s parent=%s user=%s",
        account_data.name,
        account_data.parent_account_id,
        current_user.subject,
    )
    parent_account_id = _ensure_parent_account_exists(account_service, account_data.parent_account_id)
    creation_kwargs = _build_account_creation_kwargs(account_data, parent_account_id)

    try:
        new_account = account_service.create_account(**creation_kwargs)
        logger.info(
            "Account created: id=%s name=%s user=%s",
            new_account.id,
            new_account.name,
            current_user.subject,
        )
        return _account_response_from_model(new_account, account_service)
    except ValueError as e:
        logger.warning("Account creation failed due to validation: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        logger.exception("Unexpected failure while creating account")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the account.") from None

@router.get(
    "/",
    responses={400: {"description": "Search term exceeds the allowed length or contains invalid characters."}},
)
def get_accounts(
    search_term: str | None = None,
    hidden: bool | None = None,
    placeholder: bool | None = None,
    include_hidden: str | None = None,
    include_placeholder: str | None = None,
    account_service: AccountService = account_service_dependency,
    _current_user: TokenPayload = _viewer_dependency
) -> list[AccountResponse]:
    """Retrieve a filtered list of accounts, respecting legacy query params.

    Args:
        search_term: Optional name-based filter for accounts.
        hidden: Optional filter to include only hidden or visible accounts.
        placeholder: Optional filter to include placeholder accounts.
        include_hidden: Legacy flag indicating whether to include hidden accounts.
        include_placeholder: Legacy flag indicating whether to include placeholder accounts.
        account_service: Service that provides account lookup operations.

    Returns:
        A list of AccountResponse objects matching the provided filters.

    Raises:
        HTTPException: If an invalid search term is supplied.
    """
    hidden_filter = _resolve_visibility_filter(hidden, include_hidden, default_value=False)
    placeholder_filter = _resolve_visibility_filter(placeholder, include_placeholder, default_value=False)

    sanitized_search = _sanitize_search_term(search_term)
    all_accounts = account_service.get_all_accounts()
    current_user = _resolve_current_user(_current_user)
    logger.debug(
        "Listing accounts hidden=%s placeholder=%s search=%s user=%s",
        hidden_filter,
        placeholder_filter,
        sanitized_search,
        current_user.subject,
    )

    filtered_accounts = _apply_account_filters(
        all_accounts,
        hidden_filter,
        placeholder_filter,
        sanitized_search,
    )

    return [_account_response_from_model(acc, account_service) for acc in filtered_accounts]

@router.get(
    "/{account_id}",
    responses={404: {"description": ACCOUNT_NOT_FOUND_DETAIL}},
)
def get_account_by_id(
    account_id: UUID,
    account_service: AccountService = account_service_dependency,
    _current_user: TokenPayload = _viewer_dependency
) -> AccountResponse:
    """Retrieve a specific account by its identifier.

    Args:
        account_id: The UUID of the account to return.
        account_service: Service used to retrieve the account.

    Returns:
        An AccountResponse representing the requested account.

    Raises:
        HTTPException: When the account does not exist (404).
    """
    current_user = _resolve_current_user(_current_user)
    logger.debug("Retrieving account id=%s user=%s", account_id, current_user.subject)
    account = account_service.get_account(str(account_id))
    if account is None:
        logger.warning("Account id=%s not found", account_id)
        raise HTTPException(status_code=404, detail=ACCOUNT_NOT_FOUND_DETAIL)
    return _account_response_from_model(account, account_service)

@router.put(
    "/{account_id}",
    responses={
        400: {"description": "Invalid update payload or missing/invalid parent reference."},
        404: {"description": ACCOUNT_NOT_FOUND_DETAIL},
        500: {"description": "Unexpected error while updating the account."},
    },
)
def update_account(
    account_id: UUID,
    account_data: AccountUpdatePayload,
    account_service: AccountService = account_service_dependency,
    _current_user: TokenPayload = _operator_dependency
) -> AccountResponse:
    """Update an existing account.

    Args:
        account_id: The UUID of the account to update.
        account_data: Payload containing the fields to update.
        account_service: Service that persists account updates.

    Returns:
        The updated AccountResponse.

    Raises:
        HTTPException: When the account cannot be found (404) or when validation fails (400).
    """
    # Prepare data for update, excluding fields that should not be updated or have defaults
    current_user = _resolve_current_user(_current_user)
    update_kwargs = account_data.model_dump(exclude_unset=True)
    logger.info(
        "Updating account id=%s with %s user=%s",
        account_id,
        update_kwargs,
        current_user.subject,
    )

    parent_account_id = update_kwargs.get("parent_account_id")
    if parent_account_id is not None:
        update_kwargs["parent_account_id"] = _ensure_parent_account_exists(account_service, parent_account_id)

    if "available_balance" in update_kwargs:
        quantized_balance = _quantize_amount(update_kwargs["available_balance"])
        update_kwargs["available_balance"] = float(quantized_balance)

    if "credit_limit" in update_kwargs and update_kwargs["credit_limit"] is not None:
        quantized_limit = _quantize_amount(update_kwargs["credit_limit"])
        update_kwargs["credit_limit"] = float(quantized_limit)

    try:
        updated_account = account_service.update_account(str(account_id), **update_kwargs)
    except ValueError as e:
        logger.warning("Account update rejected for id=%s: %s", account_id, e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.exception("Runtime failure updating account id=%s", account_id)
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception:
        logger.exception("Unexpected failure updating account id=%s", account_id)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating the account.") from None

    if updated_account is None:
        raise HTTPException(status_code=404, detail=ACCOUNT_NOT_FOUND_DETAIL)

    return _account_response_from_model(updated_account, account_service)

@router.delete(
    "/{account_id}",
    status_code=204,
    responses={404: {"description": ACCOUNT_NOT_FOUND_DETAIL}},
)
def delete_account(
    account_id: UUID,
    account_service: AccountService = account_service_dependency,
    _current_user: TokenPayload = _operator_dependency
) -> None:
    """Delete an account by its ID.

    Args:
        account_id: The UUID of the account to delete.
        account_service: Service responsible for account persistence.

    Returns:
        None when the account is successfully deleted.

    Raises:
        HTTPException: When the account cannot be found (404).
    """
    current_user = _resolve_current_user(_current_user)
    logger.info("Deleting account id=%s user=%s", account_id, current_user.subject)
    success = account_service.delete_account(str(account_id))
    if not success:
        logger.warning(
            "Attempted to delete missing account id=%s user=%s",
            account_id,
            current_user.subject,
        )
        raise HTTPException(status_code=404, detail=ACCOUNT_NOT_FOUND_DETAIL)
    # No content to return on successful deletion


@router.post(
    "/transactions/",
    status_code=201,
    response_model=TransactionResponse,
    responses={
        400: {"description": "Invalid transaction payload or account constraints violated."},
        500: {"description": "Unexpected error while persisting the transaction."},
    },
)
def create_transaction(
    payload: TransactionRequest,
    transaction_service: TransactionService = transaction_service_dependency,
    _current_user: TokenPayload = _operator_dependency
) -> TransactionResponse:
    """Create a balanced debit/credit transaction and update account balances atomically."""
    current_user = _resolve_current_user(_current_user)
    return _handle_transaction_request(payload, transaction_service, current_user)


@transactions_router.post(
    "/transactions/",
    status_code=201,
    response_model=TransactionResponse,
    responses={
        400: {"description": "Invalid transaction payload or account constraints violated."},
        500: {"description": "Unexpected error while persisting the transaction."},
    },
)
def create_transaction_root(
    payload: TransactionRequest,
    transaction_service: TransactionService = transaction_service_dependency,
    _current_user: TokenPayload = _operator_dependency
) -> TransactionResponse:
    """Create a balanced debit/credit transaction via the root-level contract endpoint."""
    current_user = _resolve_current_user(_current_user)
    return _handle_transaction_request(payload, transaction_service, current_user)


@quickfill_router.get(
    "/",
    response_model=list[QuickFillTemplateResponse],
    responses={
        400: {"description": "Missing or invalid QuickFill filters."},
        403: {"description": "Insufficient privileges to view pending templates."},
        500: {"description": "Unable to compute QuickFill suggestions at this time."},
    },
)
def get_quickfill_templates(
    action: ActionField,
    currency: CurrencyField,
    query: str | None = None,
    limit: int | None = 1,
    include_unapproved: bool = False,
    transaction_service: TransactionService = transaction_service_dependency,
    _current_user: TokenPayload = _viewer_dependency,
) -> list[QuickFillTemplateResponse]:
    """Return QuickFill templates filtered by action/currency + optional memo query."""
    current_user = _resolve_current_user(_current_user)
    if include_unapproved and Role.ADMIN not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only administrators can inspect pending templates.")

    normalized_limit = max(1, min(limit or 1, 25))

    try:
        candidates = transaction_service.rank_quickfill_candidates(
            action_type=action,
            currency=currency,
            query=query,
            limit=normalized_limit,
            include_unapproved=include_unapproved,
        )
    except RuntimeError as exc:
        logger.exception("QuickFill lookup failed for action=%s currency=%s", action, currency)
        raise HTTPException(status_code=500, detail="Unable to fetch QuickFill suggestions at this time.") from exc

    return [_quickfill_template_response_from_model(template) for template in candidates]


@quickfill_router.post(
    "/templates/{template_id}/approve",
    response_model=QuickFillTemplateResponse,
    responses={
        400: {"description": "Invalid template identifier."},
        404: {"description": "QuickFill template not found."},
        500: {"description": "Approval workflow failed."},
    },
)
def approve_quickfill_template(
    template_id: str,
    transaction_service: TransactionService = transaction_service_dependency,
    _current_user: TokenPayload = _admin_dependency,
) -> QuickFillTemplateResponse:
    """Approve a QuickFill template for production use."""
    current_user = _resolve_current_user(_current_user)
    try:
        template = transaction_service.approve_quickfill_template(
            template_id,
            approved_by=current_user.subject,
        )
        logger.info("QuickFill template %s approved by %s", template_id, current_user.subject)
        return _quickfill_template_response_from_model(template)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Failed to approve QuickFill template %s", template_id)
        raise HTTPException(status_code=500, detail="Unable to approve QuickFill template at this time.") from exc

@router.post(
    "/{account_id}/adjust_balance",
    responses={
        400: {"description": "Invalid adjustment payload or the target balance matches the current value."},
        500: {"description": "Unexpected error while adjusting the account balance."},
    },
)
def adjust_account_balance(
    account_id: UUID,
    request_data: BalanceAdjustmentPayload,
    transaction_service: TransactionService = transaction_service_dependency,
    _current_user: TokenPayload = _operator_dependency
) -> BalanceAdjustmentResponse:
    """Manually adjust an account's balance via a transaction.

    Args:
        account_id: Identifier of the account to adjust.
        request_data: Payload containing the target balance and metadata.
        transaction_service: Service used to perform the adjustment transaction.

    Returns:
        BalanceAdjustmentResponse summarizing the created transaction.

    Raises:
        HTTPException: When no adjustment is needed because the target matches the current balance (400)
            or when validation/runtime errors occur (400/500).
    """
    current_user = _resolve_current_user(_current_user)
    logger.info(
        "Balance adjustment request for account=%s target=%s user=%s",
        account_id,
        request_data.target_balance,
        current_user.subject,
    )
    try:
        target_balance_decimal = _quantize_amount(request_data.target_balance)
        adjustment_datetime = datetime.combine(request_data.adjustment_date, datetime.min.time())
        transaction = transaction_service.perform_balance_adjustment(
            account_id=str(account_id),
            target_balance=target_balance_decimal,
            adjustment_date=adjustment_datetime,
            description=request_data.description,
            action_type=request_data.action_type.value,
            notes=request_data.notes
        )

        if transaction is None:
            # This case happens if target_balance == current_balance, no adjustment needed.
            # Depending on requirements, this could be a 200 OK with a message, or a 400 Bad Request.
            # For now, let's raise a 400 if no adjustment was made.
            # In a real app, consider if this should return a specific response.
            logger.debug("No adjustment needed for account=%s (target equals current)", account_id)
            raise HTTPException(status_code=400, detail="No adjustment needed as target balance matches current balance.")

        transaction_data = transaction.__dict__.copy()
        logger.info(
            "Created balance adjustment transaction %s for account=%s user=%s",
            transaction.id,
            account_id,
            current_user.subject,
        )

        return BalanceAdjustmentResponse(
            transaction_id=transaction.id,
            account_id=str(account_id),
            new_balance=target_balance_decimal,
            **transaction_data
        )

    except HTTPException as http_exc:
        raise http_exc
    except ValueError as e:
        logger.warning("Invalid balance adjustment payload for account=%s: %s", account_id, e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.exception("Runtime error during balance adjustment for account=%s", account_id)
        raise HTTPException(status_code=500, detail=str(e)) from e # e.g., AccountService not set
    except Exception:
        logger.exception("Unhandled error while adjusting balance for account=%s", account_id)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during balance adjustment.") from None


@router.post(
    "/{account_id}/adjustment",
    responses={
        400: {"description": "Invalid adjustment payload or the target balance matches the current value."},
        500: {"description": "Unexpected error while adjusting the account balance."},
    },
)
def adjust_account_balance_alias(
    account_id: UUID,
    request_data: BalanceAdjustmentPayload,
    transaction_service: TransactionService = transaction_service_dependency,
    _current_user: TokenPayload = _operator_dependency
) -> BalanceAdjustmentResponse:
    return adjust_account_balance(
        account_id=account_id,
    request_data=request_data,
    transaction_service=transaction_service,
    _current_user=_current_user,
)


@router.get(
    "/duplicates/",
    response_model=list[DuplicateCandidateResponse],
    responses={400: {"description": "Missing required account_id or invalid scope."}},
)
def list_duplicate_candidates(
    account_id: UUID,
    limit: int = 25,
    transaction_service: TransactionService = transaction_service_dependency,
    _current_user: TokenPayload = _viewer_dependency,
) -> list[DuplicateCandidateResponse]:
    """List detected duplicates for a given account."""
    try:
        candidates = transaction_service.list_duplicate_candidates(account_id=str(account_id), limit=limit)
        return [_duplicate_candidate_to_response(candidate) for candidate in candidates]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/duplicates/merge",
    response_model=DuplicateMergeResponse,
    responses={400: {"description": "Invalid candidate or merge constraints violated."}},
)
def merge_duplicate_candidate(
    payload: DuplicateMergeRequest,
    transaction_service: TransactionService = transaction_service_dependency,
    _current_user: TokenPayload = _operator_dependency,
) -> DuplicateMergeResponse:
    """Merge duplicate transactions into a single canonical entry."""
    current_user = _resolve_current_user(_current_user)
    try:
        candidate, canonical_id, removed_ids, before_balance, after_balance = transaction_service.merge_duplicate_candidate(
            payload.candidate_id,
            preserve_audit=payload.preserve_audit,
            merged_by=current_user.subject,
        )
        return _duplicate_merge_response(candidate, canonical_id, removed_ids, before_balance, after_balance)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/merge",
    response_model=AccountMergePlanResponse,
    responses={400: {"description": "Invalid merge plan or depth violation."}},
)
def merge_accounts(
    payload: AccountMergePlanRequest,
    account_service: AccountService = account_service_dependency,
    transaction_service: TransactionService = transaction_service_dependency,
    _current_user: TokenPayload = _operator_dependency,
) -> AccountMergePlanResponse:
    """Merge one account into another while preserving balances and hierarchy integrity."""
    current_user = _resolve_current_user(_current_user)
    try:
        plan = account_service.merge_accounts(
            payload,
            transaction_service,
            executed_by=current_user.subject,
        )
        return _account_merge_plan_response(plan)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
