"""Router for Qatar 2022 retroactive model validation."""

import time
from fastapi import APIRouter
from app.services import backtest as backtest_service

router = APIRouter(prefix="/analysis/backtest", tags=["Backtest"])

_cache: dict = {}
_TTL = 3600  # 1-hour cache — results don't change between DB refreshes


@router.get("/qatar2022")
async def qatar_2022_backtest():
    """
    Runs the Poisson+ELO model against all 64 Qatar 2022 World Cup matches.
    Returns match-by-match predictions vs real results plus accuracy metrics.
    Result is cached for 1 hour.
    """
    cached = _cache.get("qt22")
    if cached and (time.time() - cached["ts"]) < _TTL:
        return {"success": True, **cached["data"]}

    data = backtest_service.run_qatar_2022_backtest()
    _cache["qt22"] = {"ts": time.time(), "data": data}
    return {"success": True, **data}
