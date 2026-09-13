from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="AVAX Context Engine API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status":"ok","mode":"read-only","execution":False}


@app.get("/api/v1/system")
def system() -> dict:
    return {"project":"AVAX Context Engine","execution_enabled":False,"forecast_horizons":10,"base_timeframe":"5m"}
