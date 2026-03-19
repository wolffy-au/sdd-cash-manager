"""FastAPI application entry point for sdd-cash-manager."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sdd_cash_manager.api.accounts import router as accounts_router
from sdd_cash_manager.api.v1.endpoints.adjustment import router as adjustment_router
from sdd_cash_manager.api.v1.endpoints.reconciliation import router as reconciliation_router
from sdd_cash_manager.database import create_tables

# Initialize database on startup
create_tables()

app = FastAPI(
    title="SDD Cash Manager API",
    description="API for managing accounts and transactions",
    version="0.1.0",
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (routers already define their own prefixes)
app.include_router(accounts_router)
app.include_router(adjustment_router)
app.include_router(reconciliation_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
