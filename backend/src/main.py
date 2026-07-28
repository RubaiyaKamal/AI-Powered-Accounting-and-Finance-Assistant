from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.accounts import router as accounts_router
from src.api.agent import router as agent_router
from src.api.analysis import router as analysis_router
from src.api.audit import router as audit_router
from src.api.categories import router as categories_router
from src.api.expenses import router as expenses_router
from src.api.ledger import router as ledger_router
from src.api.reconciliation import router as reconciliation_router
from src.api.reports import router as reports_router
from src.api.tax import router as tax_router
from src.config import FRONTEND_ORIGINS

app = FastAPI(title="AI-Powered Accounting Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(expenses_router)
app.include_router(categories_router)
app.include_router(agent_router)
app.include_router(accounts_router)
app.include_router(ledger_router)
app.include_router(reconciliation_router)
app.include_router(reports_router)
app.include_router(audit_router)
app.include_router(tax_router)
app.include_router(analysis_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
