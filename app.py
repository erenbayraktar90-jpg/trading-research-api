from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(
    title="Trading Research API",
    description="Daily trading research API for sector, stock and trade research automation.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Trading Research API is running",
        "time": datetime.utcnow().isoformat()
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Trading Research API is healthy",
        "time": datetime.utcnow().isoformat()
    }


@app.get("/daily-research")
def daily_research():
    return {
        "status": "ok",
        "message": "Daily Research Agent endpoint is ready.",
        "note": "Full sector and stock research logic will be added in the next step.",
        "trade_mode": "research_only",
        "live_orders": False,
        "human_approval_required": True,
        "time": datetime.utcnow().isoformat()
    }
