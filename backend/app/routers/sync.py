"""Router for live sync endpoints (ESPN scoreboard → DB)."""

from fastapi import APIRouter

from app.services import livesync

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.get("/status")
async def sync_status():
    """Last sync timestamp and API configuration status."""
    return livesync.get_sync_status()


@router.post("/run")
async def run_sync():
    """Manually trigger a WC results sync from the ESPN scoreboard."""
    result = await livesync.sync_wc_results()
    return result
