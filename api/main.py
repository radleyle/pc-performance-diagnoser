"""
FastAPI application entry point.

Run from project root:
    uvicorn api.main:app --reload
"""

import sys
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI

from api.routes import router

app = FastAPI(
    title="PC Performance Diagnoser",
    description="Local API for system metrics and performance diagnosis",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "PC Performance Diagnoser API",
        "docs": "/docs",
        "health": "/health",
    }