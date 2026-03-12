import re
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated
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
from sdd_cash_manager.schemas.account_schema import AccountResponse
from sdd_cash_manager.schemas.transaction_schema import BalanceAdjustmentResponse
from sdd_cash_manager.services.account_service import AccountService
from sdd_cash_manager.services.transaction_service import TransactionService

ALLOWED_CURRENCIES = {
    "USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "NZD", "SGD", "CNY"
}
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1F\x7F]")
NAME_ALLOWED_PATTERN = re.compile(r"^[A-Za-z0-9\s\.\,\-\_\(\)\&']+$")
MAX_SEARCH_TERM_LENGTH = 100

NameField = Annotated[str, constr(strip_whitespace=True, min_length=1, max_length=100)]
CurrencyField = Annotated[str, constr(pattern=r"^[A-Z]{3}$")]
AccountNumberField = Annotated[str, constr(strip_whitespace=True, max_length=50, pattern=r"^[A-Za-z0-9-]+$")]
BalanceField = Annotated[Decimal, condecimal(max_digits=18, decimal_places=2, ge=Decimal("0"))]
NotesField = Annotated[str, constr(strip_whitespace=True, max_length=500)]
DescriptionField = Annotated[str, constr(strip_whitespace=True, min_length=1, max_length=255)]

OptionalNameField = NameField | None
OptionalCurrencyField = CurrencyField | None
OptionalAccountNumberField = AccountNumberField | None
OptionalBalanceField = BalanceField | None
OptionalNotesField = NotesField | None

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

class AccountingCategory(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"

class BankingProductType(str, Enum):
    BANK = "BANK"
    CREDIT_CARD = "CREDIT_CARD"
    LOAN = "LOAN"
    CASH = "CASH"
    INVESTMENT = "INVESTMENT"
    OTHER = "OTHER"

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
    banking_product_type: BankingProductType
    account_number: AccountNumberField | None = None
    available_balance: BalanceField
    credit_limit: BalanceField | None = None
    notes: NotesField | None = None
    parent_account_id: UUID | None = None
    hidden: bool = False
    placeholder: bool = False

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

class AccountUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: NameField | None = None
    currency: CurrencyField | None = None
    accounting_category: AccountingCategory | None = None
    banking_product_type: BankingProductType | None = None
    account_number: AccountNumberField | None = None
    available_balance: BalanceField | None = None
    credit_limit: BalanceField | None = None
    notes: NotesField | None = None
    parent_account_id: UUID | None = None
    hidden: bool | None = None
    placeholder: bool | None = None



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


def _account_response_from_model(account: Account, account_service: AccountService) -> AccountResponse:
    """Return an AccountResponse while decrypting sensitive fields."""
    payload = account.__dict__.copy()
    decrypt_notes = getattr(account_service, "decrypt_notes", lambda value: value)
    payload["notes"] = decrypt_notes(getattr(account, "notes", None))
    payload["hierarchy_balance"] = account_service.get_account_hierarchy_balance(account.id)
    return AccountResponse(**payload)


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

def _get_transaction_service_impl(account_service: AccountService) -> TransactionService:
    """Instantiate the transaction service and attach the account service.

    Args:
        account_service: The account service used to load account data.

    Returns:
        A TransactionService configured with the account service.
    """
    ts = TransactionService()
    ts.set_account_service(account_service)
    return ts

# Module-level dependency instances (these ARE the FastAPI providers)
db_dependency = Depends(get_db)
account_service_dependency = Depends(lambda db=db_dependency: _get_account_service_impl(db=db))
transaction_service_dependency = Depends(lambda acc_svc=account_service_dependency: _get_transaction_service_impl(account_service=acc_svc))
_operator_dependency = Depends(require_role(Role.OPERATOR))
_viewer_dependency = Depends(require_role(Role.VIEWER))
logger = get_logger(__name__)

# --- API Router ---
router = APIRouter(prefix="/accounts", tags=["Accounts"])

async def _handle_request_validation_error(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )

_exception_handler = getattr(router, "add_exception_handler", None)
if _exception_handler is not None:  # pragma: no branch - runtime routers have the method
    _exception_handler(RequestValidationError, _handle_request_validation_error)

# --- Account Endpoints ---

@router.post("/", response_model=AccountResponse, status_code=201)
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
    available_balance_decimal = _quantize_amount(account_data.available_balance)
    available_balance_float = float(available_balance_decimal)
    credit_limit_decimal = (
        _quantize_amount(account_data.credit_limit)
        if account_data.credit_limit is not None
        else None
    )
    credit_limit_float = float(credit_limit_decimal) if credit_limit_decimal is not None else None

    try:
        new_account = account_service.create_account(
            name=account_data.name,
            currency=account_data.currency,
            accounting_category=account_data.accounting_category.value,
            account_number=account_data.account_number,
            banking_product_type=account_data.banking_product_type.value,
            available_balance=available_balance_float,
            credit_limit=credit_limit_float,
            notes=account_data.notes,
            parent_account_id=parent_account_id,
            hidden=account_data.hidden,
            placeholder=account_data.placeholder
        )
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

@router.get("/", response_model=list[AccountResponse])
def get_accounts(
    search_term: str | None = None,
    hidden: bool | None = None,
    placeholder: bool | None = None,
    account_service: AccountService = account_service_dependency,
    _current_user: TokenPayload = _viewer_dependency
) -> list[AccountResponse]:
    """Retrieve a filtered list of accounts.

    Args:
        search_term: Optional name-based filter for accounts.
        hidden: Optional filter to include only hidden or visible accounts.
        placeholder: Optional filter to include placeholder accounts.
        account_service: Service that provides account lookup operations.

    Returns:
        A list of AccountResponse objects matching the provided filters.

    Raises:
        HTTPException: If an invalid search term is supplied.
    """
    all_accounts = account_service.get_all_accounts()

    sanitized_search = _sanitize_search_term(search_term)
    current_user = _resolve_current_user(_current_user)
    logger.debug(
        "Listing accounts hidden=%s placeholder=%s search=%s user=%s",
        hidden,
        placeholder,
        sanitized_search,
        current_user.subject,
    )

    # Apply filters
    filtered_accounts = all_accounts
    if sanitized_search:
        filtered_accounts = [
            acc for acc in filtered_accounts
            if sanitized_search.lower() in acc.name.lower()
        ]
    if hidden is not None:
        filtered_accounts = [acc for acc in filtered_accounts if acc.hidden == hidden]
    if placeholder is not None:
        filtered_accounts = [acc for acc in filtered_accounts if acc.placeholder == placeholder]

    return [_account_response_from_model(acc, account_service) for acc in filtered_accounts]

@router.get("/{account_id}", response_model=AccountResponse)
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
        raise HTTPException(status_code=404, detail="Account not found")
    return _account_response_from_model(account, account_service)

@router.put("/{account_id}", response_model=AccountResponse)
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
        update_kwargs["available_balance"] = float(_quantize_amount(update_kwargs["available_balance"]))
    if "credit_limit" in update_kwargs and update_kwargs["credit_limit"] is not None:
        update_kwargs["credit_limit"] = float(_quantize_amount(update_kwargs["credit_limit"]))

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
        raise HTTPException(status_code=404, detail="Account not found")

    return _account_response_from_model(updated_account, account_service)

@router.delete("/{account_id}", status_code=204)
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
        raise HTTPException(status_code=404, detail="Account not found")
    # No content to return on successful deletion
    return

# --- Balance Adjustment Endpoint ---

@router.post("/{account_id}/adjust_balance", response_model=BalanceAdjustmentResponse)
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
            target_balance=float(target_balance_decimal),
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
            new_balance=float(target_balance_decimal),
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
