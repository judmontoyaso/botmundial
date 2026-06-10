"""
Live sync service — fetches finished WC2026 results from the public ESPN
scoreboard API, updates match scores, recalculates ELO, and updates team
form stats.

Nota: antes se usaba API-Football, pero su plan gratuito NO da acceso a la
temporada 2026 ("Free plans do not have access to this season"), por lo que
el sync nunca traía datos. ESPN es pública, sin API key, y es la misma
fuente con la que se corrigió el calendario oficial (fix_schedule.py).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.services import data_service

logger = logging.getLogger("app.services.livesync")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
)
# Ventana completa del torneo (UTC), en bloques para no exceder el límite
# de eventos por respuesta del scoreboard.
_WC_DATE_RANGES = [
    "20260611-20260620",
    "20260621-20260630",
    "20260701-20260710",
    "20260711-20260720",
]
_ELO_K = 60             # High K-factor for World Cup (most important competition)

# State
_last_sync: Optional[datetime] = None
_last_result: dict = {}

# ---------------------------------------------------------------------------
# ESPN team name → our FIFA 3-letter code (fallback cuando la abreviatura
# de ESPN no coincide con nuestro código)
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
    "Bosnia and Herzegovina": "BIH", "Bosnia-Herzegovina": "BIH",
    "Türkiye": "TUR", "Greece": "GRE",
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
    "DR Congo": "COD", "Congo DR": "COD", "Mali": "MLI",
    "Cape Verde": "CPV", "Sudan": "SDN",
    # CONCACAF adicionales
    "Curaçao": "CUW", "Curacao": "CUW",
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
# ESPN fetcher
# ---------------------------------------------------------------------------

async def _fetch_finished_fixtures() -> list[dict]:
    """
    Fetch finished WC2026 fixtures from the ESPN public scoreboard.
    Returns normalized dicts: {home_name, away_name, home_abbr, away_abbr,
    home_goals, away_goals, date}.
    """
    events: dict[str, dict] = {}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for rng in _WC_DATE_RANGES:
                resp = await client.get(
                    _ESPN_SCOREBOARD, params={"dates": rng, "limit": 200}
                )
                resp.raise_for_status()
                for e in resp.json().get("events", []):
                    events[e["id"]] = e
    except httpx.HTTPStatusError as e:
        logger.error("ESPN HTTP error: %s", e)
        return []
    except Exception as e:
        logger.error("ESPN fetch failed: %s", e)
        return []

    finished = []
    for e in events.values():
        status_type = (e.get("status") or {}).get("type", {})
        if not status_type.get("completed"):
            continue
        comp = (e.get("competitions") or [{}])[0]
        sides: dict[str, dict] = {}
        for c in comp.get("competitors", []):
            sides[c.get("homeAway", "")] = c
        home, away = sides.get("home"), sides.get("away")
        if not home or not away:
            continue
        try:
            home_goals = int(home.get("score"))
            away_goals = int(away.get("score"))
        except (TypeError, ValueError):
            continue
        finished.append({
            "home_name": home["team"].get("displayName", ""),
            "away_name": away["team"].get("displayName", ""),
            "home_abbr": home["team"].get("abbreviation", ""),
            "away_abbr": away["team"].get("abbreviation", ""),
            "home_goals": home_goals,
            "away_goals": away_goals,
            "date": e.get("date", ""),
        })
    logger.info("ESPN: %d finished fixtures of %d events", len(finished), len(events))
    return finished


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------

def _resolve_code(name: str, abbr: str = "") -> Optional[str]:
    # ESPN abbreviations usually match our FIFA codes directly
    if abbr and any(t.code == abbr for t in data_service.load_teams()):
        return abbr
    code = _NAME_TO_CODE.get(name)
    if code:
        return code
    # Fallback: check if our DB has a team whose name partially matches
    for team in data_service.load_teams():
        if team.name.lower() == name.lower():
            return team.code
    return None


def _process_fixture(fix: dict) -> Optional[tuple[str, str]]:
    """
    Apply a single finished fixture (normalized ESPN dict) to our DB.
    Returns (home_code, away_code) if the match was newly synced,
    None if unknown or already up-to-date.
    """
    date_str = (fix.get("date") or "")[:10]  # YYYY-MM-DD (UTC)
    home_goals = fix["home_goals"]
    away_goals = fix["away_goals"]

    home_code = _resolve_code(fix["home_name"], fix["home_abbr"])
    away_code = _resolve_code(fix["away_name"], fix["away_abbr"])
    if not home_code or not away_code:
        logger.debug(
            "Unknown team names: '%s' vs '%s'", fix["home_name"], fix["away_name"]
        )
        return None

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
        return None

    # Skip if already synced with same scores
    if (our_match.status.value == "completed"
            and our_match.home_score == home_goals
            and our_match.away_score == away_goals):
        return None

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

    return home_code, away_code


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def sync_wc_results() -> dict:
    """
    Fetch all finished WC2026 results and apply any new ones to the DB.
    Called periodically by the background task and manually via /api/sync/run.
    """
    global _last_sync, _last_result

    fixtures = await _fetch_finished_fixtures()
    total = len(fixtures)

    synced = 0
    errors = 0
    affected_teams: set[str] = set()
    for fix in fixtures:
        try:
            codes = _process_fixture(fix)
            if codes:
                synced += 1
                affected_teams.update(codes)
        except Exception as e:
            errors += 1
            logger.warning("Error processing fixture: %s", e)

    # New results changed ELO/form → refresh cached AI predictions for the
    # upcoming matches of the affected teams (off the event loop).
    refreshed = 0
    if affected_teams:
        try:
            from app.services import predictor
            refreshed = await asyncio.to_thread(
                predictor.refresh_predictions_for_teams, affected_teams
            )
            logger.info("AI predictions refreshed for %s: %d", affected_teams, refreshed)
        except Exception as e:
            logger.error("Prediction refresh failed: %s", e)

    _last_sync = datetime.now(timezone.utc)
    _last_result = {
        "success": True,
        "synced": synced,
        "total_finished": total,
        "errors": errors,
        "predictions_refreshed": refreshed,
        "synced_at": _last_sync.isoformat(),
    }
    logger.info("Sync done: %d/%d new, %d errors", synced, total, errors)
    return _last_result


def get_sync_status() -> dict:
    return {
        "last_sync": _last_sync.isoformat() if _last_sync else None,
        "last_result": _last_result,
        # ESPN es pública: no requiere API key
        "api_configured": True,
        "source": "espn",
    }
