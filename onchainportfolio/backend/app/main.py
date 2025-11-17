# app/main.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, balances, prices, portfolio
from .routers.auth import router as auth_router
app = FastAPI(title="On-Chain Portfolio API", version="0.1.0")

# 🔓 CORS so frontend (Vite) can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routers
app.include_router(health.router, tags=["health"])
app.include_router(balances.router, prefix="/v1", tags=["wallets"])
app.include_router(prices.router, prefix="/v1", tags=["prices"])
app.include_router(portfolio.router, prefix="/v1", tags=["portfolio"])

# 🆕 Auth router (paths start with /auth because of prefix in auth router)
app.include_router(auth_router)


# Add a root route so GET / doesn’t 404
@app.get("/", include_in_schema=False)
def root():
    # Option A: Simple message
    # return {"message": "On-Chain Portfolio API — see /docs for Swagger UI"}

    # Option B (recommended during dev): redirect to Swagger UI
    return RedirectResponse(url="/docs")
