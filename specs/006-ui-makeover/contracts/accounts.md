# API Contract: Accounts

All endpoints are served by the existing FastAPI backend (`src/sdd_cash_manager/api/accounts.py`).
Base URL: `http://localhost:8000` (dev) — configure via `VITE_API_BASE_URL` env var.
Authentication: `Authorization: Bearer {token}` — attached by Axios interceptor reading `localStorage['auth-token']`.

---

## GET /accounts/

Retrieve all accounts as a flat list. The frontend builds the tree client-side.

**Auth**: VIEWER role minimum.

**Query params** (all optional):

| Param | Type | Default | Notes |
|---|---|---|---|
| `include_hidden` | `"true"\|"false"` | `"false"` | Pass `"true"` to include hidden accounts |
| `include_placeholder` | `"true"\|"false"` | `"false"` | Pass `"true"` to include placeholder accounts |
| `search_term` | `string` | — | Substring match on `name` (max 100 chars) |

**Frontend call**: `GET /accounts/?include_hidden=true&include_placeholder=true`
(Filter dialog controls visibility client-side after fetching all accounts.)

**Response** `200 OK`: `AccountResponse[]`

```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Checking",
    "currency": "AUD",
    "accounting_category": "ASSET",
    "banking_product_type": "BANK",
    "account_number": "507941889",
    "available_balance": "12430.20",
    "hierarchy_balance": "12430.20",
    "credit_limit": null,
    "notes": null,
    "parent_account_id": "parent-uuid",
    "hidden": false,
    "placeholder": false
  }
]
```

**Error responses**: `400` (invalid search term), `401` (unauthenticated).

---

## POST /accounts/

Create a new account.

**Auth**: OPERATOR role minimum.

**Request body** (`AccountCreatePayload`):

```json
{
  "name": "New Savings",
  "currency": "AUD",
  "accounting_category": "ASSET",
  "banking_product_type": "BANK",
  "account_number": "123456-789",
  "available_balance": "0.00",
  "placeholder": false,
  "hidden": false,
  "parent_account_id": "parent-uuid-or-null",
  "notes": "Optional description"
}
```

**Field constraints**:
- `name`: required, 1–100 chars, alphanumeric + `. , - _ ( ) & '`
- `currency`: required, 3-char ISO 4217 code (AUD, USD, EUR, GBP, CAD, JPY, CHF, NZD, SGD, CNY)
- `accounting_category`: `ASSET | LIABILITY | EQUITY | REVENUE | EXPENSE`
- `banking_product_type`: `BANK | CREDIT_CARD | LOAN | CASH | INVESTMENT | OTHER`
- `account_number`: optional, alphanumeric + dashes only
- `available_balance`: ≥ 0, max 18 digits, 2 decimal places

**Response** `201 Created`: `AccountResponse` (same shape as GET item above).

**Error responses**: `400` (validation failure or parent not found), `401`, `500`.

---

## PUT /accounts/{account_id}

Update an existing account. Only fields included in the request body are changed (patch semantics via `model_dump(exclude_unset=True)`).

**Auth**: OPERATOR role minimum.

**Request body** (`AccountUpdatePayload`) — all fields optional:

```json
{
  "name": "Renamed Account",
  "hidden": true
}
```

**Response** `200 OK`: Updated `AccountResponse`.

**Error responses**: `400` (validation), `401`, `404` (account not found), `500`.

---

## DELETE /accounts/{account_id}

Delete an account permanently.

**Auth**: OPERATOR role minimum.

**Response** `204 No Content`.

**Error responses**: `401`, `404` (account not found).

---

## Frontend mutation → cache invalidation flow

```
User clicks OK in AccountDialog
  → useMutation fires POST or PUT
    → on success: queryClient.invalidateQueries({ queryKey: ['accounts'] })
      → useQuery(['accounts']) refetches GET /accounts/?include_hidden=true&include_placeholder=true
        → buildAccountTree() rebuilds the tree
          → AccountTree re-renders with updated data
```

Delete flow is identical but fires DELETE and confirms with `DeleteConfirmDialog` first.
