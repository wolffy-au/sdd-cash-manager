# API Contracts: SDD Cash Manager Httpx Pytest Suite

## POST /accounts
- **Purpose**: Create a new ledger account.
- **Request**
  - Headers: `Authorization: Bearer <JWT>`
  - Body:
    ```json
    {
      "name": "string",
      "currency": "USD",
      "accounting_category": "ASSET|LIABILITY|EQUITY",
      "banking_product_type": "CHECKING|SAVINGS",
      "notes": "optional string"
    }
    ```
- **Response (201 Created)**:
  ```json
  {
    "id": "uuid",
    "name": "string",
    "currency": "USD",
    "accounting_category": "ASSET|LIABILITY|EQUITY",
    "available_balance": "decimal",
    "hidden": false,
    "placeholder": false
  }
  ```

## GET /accounts
- **Purpose**: List accounts with optional filters.
- **Query Parameters**:
  - `search_term` (optional string)
  - `include_hidden` (boolean)
  - `include_placeholder` (boolean)
- **Response (200 OK)**:
  ```json
  {
    "accounts": [
      {
        "id": "uuid",
        "name": "string",
        "hidden": boolean,
        "placeholder": boolean
      }
    ]
  }
  ```

## POST /accounts/{account_id}/adjustment
- **Purpose**: Record a balance adjustment (transaction).
- **Request Body**:
  ```json
  {
    "amount": "decimal",
    "action_type": "CREDIT|DEBIT",
    "description": "string"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "transaction_id": "uuid",
    "status": "COMPLETED",
    "entries": [
      {
        "account_id": "uuid",
        "amount": "decimal"
      }
    ]
  }
  ```

## GET /accounts/{account_id}/balance
- **Purpose**: Retrieve the latest balance for a single account after adjustments.
- **Response (200 OK)**:
  ```json
  {
    "id": "uuid",
    "available_balance": "decimal"
  }
  ```

## Error Responses
- **Validation Failure (422)**: Returns a JSON body with `detail` array describing missing or invalid fields (e.g., `"currency must be 3-letter code"`).
- **Authentication Failure (401)**: Returns `{ "detail": "Not authenticated" }`.
