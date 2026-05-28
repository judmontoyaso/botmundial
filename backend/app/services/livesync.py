"""
Live sync service — fetches finished WC2026 results from API-Football,
updates match scores, recalculates ELO, and updates team form stats.

API-Football docs: https://www.api-football.com/documentation-v3
Free tier: 100 req/day via api-sports.io or RapidAPI.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import get_settings
from app.services import data_service

logger = logging.getLogger("app.services.livesync")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_APIF_BASE = "https://v3.football.api-sports.io"
_WC_LEAGUE_ID = 1       # FIFA World Cup on API-Football
_WC_SEASON = 2026
_ELO_K = 60             # High K-factor for World Cup (most important competition)

# State
_last_sync: Optional[datetime] = None
_last_result: dict = {}

# ---------------------------------------------------------------------------
# API-Football team name → our FIFA 3-letter code
# Teams confirmed for WC2026 (CONCACAF, CONMEBOL, UEFA, AFC, CAF, OFC)
# ---------------------------------------------------------------------------
_NAME_TO_CODE: dict[str, str] = {
    # CONCACAF (host nations + qualifiers)
    "Mexico": "MEX", "United States": "USA", "Canada": "CAN",
    "Costa Rica": "CRC", "Panama": "PAN", "Honduras": "HON",
    "Jamaica": "JAM", "Haiti": "HAI", "Trinidad and Tobago": "TRI",
    "El Salvador": "SLV", "Guatemala": "GUA", "Cuba": "CUB",
    # CONMEBOL
    "Argentina": "ARG", "Brazil": "BRA", "Colombia": "COL",
    "Uruguay": "URU", "Ecuador": "ECU", "Chile": "CHI",
    "Venezuela": "VEN", "Peru": "PER", "Paraguay": "PAR", "Bolivia": "BOL",
    # UEFA
    "France": "FRA", "England": "ENG", "Spain": "ESP", "Germany": "GER",
    "Portugal": "POR", "Netherlands": "NED", "Belgium": "BEL",
    "Italy": "ITA", "Croatia": "CRO", "Switzerland": "SUI",
    "Austria": "AUT", "Turkey": "TUR", "Scotland": "SCO",
    "Albania": "ALB", "Serbia": "SRB", "Slovenia": "SVN",
    "Hungary": "HUN", "Romania": "ROU", "Slovakia": "SVK",
    "Ukraine": "UKR", "Czech Republic": "CZE", "Czechia": "CZE",
    "Bosnia and Herzegovina": "BIH", "Greece": "GRE",
    "Norway": "NOR", "Sweden": "SWE", "Denmark": "DEN", "Poland": "POL",
    "Georgia": "GEO", "Iceland": "ISL", "Wales": "WAL", "Finland": "FIN",
    # AFC
    "Japan": "JPN", "South Korea": "KOR", "Korea Republic": "KOR",
    "Australia": "AUS", "Iran": "IRN", "Saudi Arabia": "KSA",
    "Jordan": "JOR", "Qatar": "QAT", "Iraq": "IRQ", "Uzbekistan": "UZB",
    "Indonesia": "IDN", "Bahrain": "BHR", "Oman": "OMA",
    # CAF
    "Morocco": "MAR", "Egypt": "EGY", "Nigeria": "NGA",
    "Cameroon": "CMR", "Senegal": "SEN", "Ivory Coast": "CIV",
    "Côte d'Ivoire": "CIV", "Ghana": "GHA", "Tunisia": "TUN",
    "Algeria": "ALG", "South Africa": "RSA",
    "DR Congo": "DRC", "Congo DR": "DRC", "Mali": "MLI",
    "Cape Verde": "CPV", "Sudan": "SDN",
    # OFC
    "New Zealand": "NZL",
}


# ---------------------------------------------------------------------------
# ELO calculation
# ---------------------------------------------------------------------------

def _elo_update(
    home_elo: int, away_elo: int, home_goals: int, away_goals: int
) -> tuple[int, int]:
    """Standard ELO update using World Cup K-factor of 60."""
    expected_home = 1.0 / (1.0 + 10.0 ** ((away_elo - home_elo) / 400.0))
    if home_goals > away_goals:
        actual_home = 1.0
    elif home_goals == away_goals:
        actual_home = 0.5
    else:
        actual_home = 0.0
    new_home = round(home_elo + _ELO_K * (actual_home - expected_home))
    new_away = round(away_elo + _ELO_K * ((1.0 - actual_home) - (1.0 - expected_home)))
    return new_home, new_away


# ---------------------------------------------------------------------------
# API-Football fetcher
# ---------------------------------------------------------------------------

async def _fetch_fixtures(status: str = "FT") -> list[dict]:
    """
    Fetch WC2026 fixtures with the given status from API-Football.
    status: 'FT' (finished), 'LIVE' (1H/2H/HT/ET/P), 'NS' (not started)
    Returns the raw 'response' list from the API.
    """
    settings = get_settings()
    key = settings.API_FOOTBALL_KEY
    if not key:
        logger.warning("API_FOOTBALL_KEY not set — skipping fetch")
        return []

    headers = {"x-apisports-key": key}
    params = {"league": _WC_LEAGUE_ID, "season": _WC_SEASON, "status": status}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{_APIF_BASE}/fixtures", params=params, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
            remaining = resp.headers.get("x-ratelimit-requests-remaining", "?")
            logger.info(
                "API-Football: %d fixtures (status=%s), %s requests remaining",
                len(payload.get("response", [])), status, remaining,
            )
            return payload.get("response", [])
    except httpx.HTTPStatusError as e:
        logger.error("API-Football HTTP error: %s", e)
        return []
    except Exception as e:
        logger.error("API-Football fetch failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------

def _resolve_code(name: str) -> Optional[str]:
    code = _NAME_TO_CODE.get(name)
    if code:
        return code
    # Fallback: check if our DB has a team whose name partially matches
    for team in data_service.load_teams():
        if team.name.lower() == name.lower():
            return team.code
    return None


def _process_fixture(fix: dict) -> bool:
    """
    Apply a single finished fixture to our DB.
    Returns True if the match was newly synced, False if already up-to-date.
    """
    teams = fix.get("teams", {})
    goals = fix.get("goals", {})
    date_str = (fix.get("fixture", {}).get("date") or "")[:10]  # YYYY-MM-DD

    home_name = teams.get("home", {}).get("name", "")
    away_name = teams.get("away", {}).get("name", "")
    home_goals = goals.get("home")
    away_goals = goals.get("away")

    if home_goals is None or away_goals is None:
        return False

    home_code = _resolve_code(home_name)
    away_code = _resolve_code(away_name)
    if not home_code or not away_code:
        logger.debug("Unknown team names: '%s' vs '%s'", home_name, away_name)
        return False

    # Find our matching fixture by team codes + date
    our_matches = data_service.load_matches()
    our_match = next(
        (m for m in our_matches
         if m.home_team_code == home_code
         and m.away_team_code == away_code
         and str(m.match_date)[:10] == date_str),
        None,
    )
    if our_match is None:
        logger.debug("No local match found for %s vs %s on %s", home_code, away_code, date_str)
        return False

    # Skip if already synced with same scores
    if (our_match.status.value == "finished"
            and our_match.home_score == home_goals
            and our_match.away_score == away_goals):
        return False

    # Update match result in DB
    data_service.update_match_result(our_match.id, home_goals, away_goals)
    logger.info("Match synced: %s %d-%d %s (%s)", home_code, home_goals, away_goals, away_code, date_str)

    # Update ELO for both teams
    home_team = data_service.get_team_by_code(home_code)
    away_team = data_service.get_team_by_code(away_code)
    if home_team and away_team:
        old_h, old_a = home_team.stats.elo_rating, away_team.stats.elo_rating
        new_h, new_a = _elo_update(old_h, old_a, home_goals, away_goals)
        data_service.update_team_elo(home_code, new_h)
        data_service.update_team_elo(away_code, new_a)
        logger.info(
            "ELO: %s %d→%d | %s %d→%d",
            home_code, old_h, new_h, away_code, old_a, new_a,
        )

    # Update rolling form stats
    data_service.update_team_form_after_match(home_code, home_goals, away_goals)
    data_service.update_team_form_after_match(away_code, away_goals, home_goals)

    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def sync_wc_results() -> dict:
    """
    Fetch all finished WC2026 results and apply any new ones to the DB.
    Called periodically by the background task and manually via /api/sync/run.
    """
    global _last_sync, _last_result

    fixtures = await _fetch_fixtures("FT")
    total = len(fixtures)

    synced = 0
    errors = 0
    for fix in fixtures:
        try:
            if _process_fixture(fix):
                synced += 1
        except Exception as e:
            errors += 1
            logger.warning("Error processing fixture: %s", e)

    _last_sync = datetime.now(timezone.utc)
    _last_result = {
        "success": True,
        "synced": synced,
        "total_finished": total,
        "errors": errors,
        "synced_at": _last_sync.isoformat(),
    }
    logger.info("Sync done: %d/%d new, %d errors", synced, total, errors)
    return _last_result


def get_sync_status() -> dict:
    return {
        "last_sync": _last_sync.isoformat() if _last_sync else None,
        "last_result": _last_result,
        "api_configured": bool(get_settings().API_FOOTBALL_KEY),
    }
