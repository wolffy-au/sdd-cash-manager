# Public API Contract: Account Management

This document defines the public API contract for the Account Management feature. It specifies the interfaces exposed by the library/API, detailing request and response formats, and operational contracts.

## API Endpoints

The primary interface is a RESTful API. All endpoints expect and return JSON payloads. Base URL is assumed to be `http://localhost:8000` for local development.

### Account Management

#### `POST /accounts`

**Description**: Creates a new financial account.
**Request Body**:
```json
{
  "account_number": "string (unique)",
  "name": "string",
  "currency": "string (e.g., USD)",
  "accounting_category": "string (e.g., Asset)",
  "banking_product_type": "string (e.g., Checking)",
  "available_balance": "decimal (optional, defaults to 0)",
  "credit_limit": "decimal (optional)",
  "notes": "string (optional)",
  "parent_account_id": "uuid (optional)"
}
```
**Response (201 Created)**:
```json
{
  "id": "uuid",
  "account_number": "string",
  "name": "string",
  "currency": "string",
  "accounting_category": "string",
  "banking_product_type": "string",
  "available_balance": "decimal",
  "credit_limit": "decimal (optional)",
  "notes": "string (optional)",
  "parent_account_id": "uuid (optional)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```
**Errors**: 400 Bad Request, 409 Conflict (account number exists).

#### `GET /accounts`

**Description**: Retrieves a list of accounts. Supports filtering and pagination.
**Query Parameters**:
- `search_term` (string, optional): Filter accounts by name.
- `parent_id` (uuid, optional): Filter by parent account ID for hierarchical view.
- `limit` (integer, optional, default 20): Number of results per page.
- `offset` (integer, optional, default 0): Offset for pagination.
**Response (200 OK)**:
```json
{
  "accounts": [
    {
      "id": "uuid",
      "account_number": "string",
      "name": "string",
      "currency": "string",
      "accounting_category": "string",
      "banking_product_type": "string",
      "available_balance": "decimal",
      "credit_limit": "decimal (optional)",
      "notes": "string (optional)",
      "parent_account_id": "uuid (optional)",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ],
  "total": "integer",
  "limit": "integer",
  "offset": "integer"
}
```
**Errors**: 400 Bad Request.

#### `GET /accounts/{id}`

**Description**: Retrieves details for a specific account.
**Path Parameters**:
- `id` (uuid): The ID of the account to retrieve.
**Response (200 OK)**:
```json
{
  "id": "uuid",
  "account_number": "string",
  "name": "string",
  "currency": "string",
  "accounting_category": "string",
  "banking_product_type": "string",
  "available_balance": "decimal",
  "credit_limit": "decimal (optional)",
  "notes": "string (optional)",
  "parent_account_id": "uuid (optional)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```
**Errors**: 404 Not Found, 400 Bad Request.

#### `PUT /accounts/{id}`

**Description**: Updates an existing financial account.
**Path Parameters**:
- `id` (uuid): The ID of the account to update.
**Request Body**:
```json
{
  "name": "string (optional)",
  "currency": "string (optional)",
  "accounting_category": "string (optional)",
  "banking_product_type": "string (optional)",
  "available_balance": "decimal (optional)",
  "credit_limit": "decimal (optional)",
  "notes": "string (optional)",
  "parent_account_id": "uuid (optional)"
}
```
**Response (200 OK)**: Updated account object.
**Errors**: 404 Not Found, 400 Bad Request, 409 Conflict.

#### `DELETE /accounts/{id}`

**Description**: Deletes a financial account.
**Path Parameters**:
- `id` (uuid): The ID of the account to delete.
**Response (204 No Content)**:
**Errors**: 404 Not Found, 400 Bad Request, 403 Forbidden (if account has transactions or is a parent account).

#### `POST /accounts/{id}/adjust_balance`

**Description**: Manually adjusts the balance of an account, creating a corresponding transaction.
**Path Parameters**:
- `id` (uuid): The ID of the account to adjust.
**Request Body**:
```json
{
  "adjustment_amount": "decimal",
  "description": "string",
  "effective_date": "date (optional)",
  "booking_date": "date (optional)",
  "action_type": "string (e.g., 'adjustment')"
}
```
**Response (201 Created)**: Transaction object representing the adjustment.
**Errors**: 404 Not Found, 400 Bad Request (e.g., insufficient funds if applicable, invalid amount).

### Transaction Management (Indirect via Account Adjustments)

*Details on direct transaction management are outside the scope of Account Management API, but transactions are created via account adjustments.*

## Enum Definitions (API Representation)

-   **`AccountingCategoryType`**: `["Asset", "Liability", "Equity", "Revenue", "Expense"]`
-   **`BankingAccountType`**: `["Checking", "Savings", "CreditCard", "Loan", "Investment"]`
-   **`ProcessingStatus`**: `["Pending", "Processed", "Failed"]`
-   **`ReconciliationStatus`**: `["Unreconciled", "Reconciled"]`

## Data Types

-   **UUID**: Standard UUID format (e.g., `a1b2c3d4-e5f6-7890-1234-567890abcdef`).
-   **Decimal**: Represented as a string for precision in JSON, or a floating-point number if the API framework handles it appropriately.
-   **DateTime**: ISO 8601 format (e.g., `YYYY-MM-DDTHH:MM:SSZ`).
-   **Date**: ISO 8601 format (e.g., `YYYY-MM-DD`).

## Notes

-   Authentication and authorization mechanisms are handled by the overarching API framework and are not detailed in this contract.
-   Error responses should include a consistent format detailing the error type and message.
