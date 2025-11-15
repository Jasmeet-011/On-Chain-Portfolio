from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .routers import health, balances, prices, portfolio

app = FastAPI(title="On-Chain Portfolio API", version="0.1.0")


app.include_router(health.router, tags=["health"])
app.include_router(balances.router, prefix="/v1", tags=["wallets"])
app.include_router(prices.router, prefix="/v1", tags=["prices"])
app.include_router(portfolio.router, prefix="/v1", tags=["portfolio"])


# Add a root route so GET / doesn’t 404
@app.get("/", include_in_schema=False)
def root():
    # Option A: Simple message
    # return {"message": "On-Chain Portfolio API — see /docs for Swagger UI"}

    # Option B (recommended during dev): redirect to Swagger UI
    return RedirectResponse(url="/docs")