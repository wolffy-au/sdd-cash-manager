# Public API Contract

This document details the public API endpoints for the Account Management feature, defining the request and response contracts for each operation, updated for double-entry accounting.

## Base URL

The API is served from a base URL, typically `http://localhost:8000` or a deployed domain.

## Authentication & Authorization

* **Authentication**: RS256 JWT based on OAuth 2.0 standards.
* **Authorization**: Role-Based Access Control (RBAC) will be enforced.

## Endpoints

### 1. Create Account

* **Method**: `POST`
* **Path**: `/accounts/`
* **Description**: Creates a new financial account.
* **Request Body (`AccountCreatePayload`)**:
  * `name`: String (max_length=100, specific allowed chars) - Required.
  * `currency`: String (3 uppercase letters, ISO 4217) - Required.
  * `accounting_category`: Enum (`AccountingCategory`) - Required.
  * `banking_product_type`: Enum (`BankingProductType`) - Required.
  * `account_number`: Optional String (max_length=50, alphanumeric/hyphens)
  * `available_balance`: Decimal (max_digits=18, decimal_places=2, ge=0, quantized to 0.01) - Required. **Note**: This initial balance will be represented as a double-entry transaction upon account creation.
  * `credit_limit`: Optional Decimal (same constraints as `available_balance`)
  * `notes`: Optional String (max_length=500, specific allowed chars)
  * `parent_account_id`: Optional UUID (must reference existing account)
  * `hidden`: Boolean - Defaults to `False`.
  * `placeholder`: Boolean - Defaults to `False`.
* **Response Body (Success `201 Created`)**:
  * Details of the created `Account` object.

### 2. List Accounts / Search Accounts

* **Method**: `GET`
* **Path**: `/accounts/`
* **Description**: Retrieves a list of accounts, with optional search and filtering.
* **Query Parameters**:
  * `search_term`: Optional String (max_length=100, trimmed, no control chars) - For partial name matching.
  * `hidden`: Optional Boolean - Filter by hidden status.
  * `placeholder`: Optional Boolean - Filter by placeholder status.
* **Response Body (Success `200 OK`)**:
  * A list of `Account` objects.

### 3. Get Specific Account

* **Method**: `GET`
* **Path**: `/accounts/{account_id}`
* **Description**: Retrieves details for a specific account.
* **Path Parameters**:
  * `account_id`: UUID - The ID of the account to retrieve.
* **Response Body (Success `200 OK`)**:
  * Details of the specified `Account` object.

### 4. Update Account

* **Method**: `PUT`
* **Path**: `/accounts/{account_id}`
* **Description**: Updates an existing financial account.
* **Path Parameters**:
  * `account_id`: UUID - The ID of the account to update.
* **Request Body (`AccountUpdatePayload`)**:
  * Optional fields to update, using similar validation rules as `AccountCreatePayload` (e.g., `name`, `currency`, `notes`, `credit_limit`).
  * **Note**: `available_balance` cannot be directly updated via this endpoint; balance adjustments are handled by dedicated endpoints that create transactions.
  * `parent_account_id` validated to exist.
* **Response Body (Success `200 OK`)**:
  * Details of the updated `Account` object.

### 5. Delete Account

* **Method**: `DELETE`
* **Path**: `/accounts/{account_id}`
* **Description**: Deletes a specific account. **Note**: Deletion of accounts with associated transactions may be restricted or require special handling.
* **Path Parameters**:
  * `account_id`: UUID - The ID of the account to delete.
* **Response Body (Success `204 No Content`)**:
  * Indicates successful deletion.

### 6. Adjust Account Balance

* **Method**: `POST`
* **Path**: `/accounts/{account_id}/adjust_balance`
* **Description**: Manually adjusts an account's balance by creating a double-entry `Transaction` with corresponding `Entries`. This replaces the single-entry adjustment mechanism.
* **Path Parameters**:
  * `account_id`: UUID - The primary account ID associated with this adjustment. The system will determine the corresponding debit/credit accounts based on the adjustment type and account category.
* **Request Body (`BalanceAdjustmentPayload`)**:
  * `adjustment_date`: Date/DateTime - The date for the adjustment transaction.
  * `description`: String (min_length=1, max_length=255, specific allowed chars) - Description of the adjustment.
  * `action_type`: Enum (`ActionType`) - Type of adjustment action (e.g., 'ManualAdjustment', 'Correction').
  * `amount`: Decimal (max_digits=18, decimal_places=2, ge=0, quantized to 0.01) - The absolute value of the adjustment. The system determines debit/credit based on `action_type` and target account.
  * `debit_account_id`: UUID - The ID of the account to be debited. Must reference an existing account.
  * `credit_account_id`: UUID - The ID of the account to be credited. Must reference an existing account.
  * `notes`: Optional String (max_length=500, specific allowed chars) - Additional notes for the adjustment.
* **Response Body (Success `200 OK`)**:
  * Details of the created `Transaction` object representing the adjustment, including its associated `Entries`.

## Error Handling

* **`400 Bad Request`**: For invalid input, schema validation failures, malformed requests, or double-entry integrity violations (e.g., debits not equaling credits).
* **`401 Unauthorized`**: If authentication fails.
* **`403 Forbidden`**: If the authenticated user lacks permissions (RBAC).
* **`404 Not Found`**: If a requested resource (e.g., account\_id, transaction\_id) does not exist.
* **`500 Internal Server Error`**: For unexpected server-side issues.

## Security Considerations

* All sensitive data should be transmitted over TLS 1.3.
* Data at rest should be encrypted using AES-256.
* Input validation must be strictly enforced to prevent injection attacks (e.g., SQL injection, XSS).
* Double-entry integrity checks must be performed before committing transactions.
