from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.agent import router as agent_router
from src.api.categories import router as categories_router
from src.api.expenses import router as expenses_router

app = FastAPI(title="AI-Powered Accounting Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(expenses_router)
app.include_router(categories_router)
app.include_router(agent_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
