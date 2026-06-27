"""Data service – Supabase-only. No JSON fallbacks."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.models.match import Match, MatchStatus, MatchWithTeams
from app.models.prediction import MyPrediction, MyPredictionCreate, AIPrediction
from app.models.team import Team, TeamStats
from app.supabase_client import supabase

logger = logging.getLogger("app.services.data_service")

# ---------------------------------------------------------------------------
# In-memory team cache — eliminates N×2 Supabase round-trips on /matches
# ---------------------------------------------------------------------------
_teams_by_code: dict[str, Team] = {}   # code → Team
_team_id_to_code: dict[int, str] = {}  # db_id → code
_teams_loaded: bool = False


# FIFA 3-letter → ISO 3166-1 alpha-2 for flagcdn.com URLs
_FIFA_TO_ISO2: dict[str, str] = {
    "MEX": "mx", "USA": "us", "CAN": "ca", "CRC": "cr", "PAN": "pa",
    "HON": "hn", "JAM": "jm", "HAI": "ht", "CUW": "cw", "TRI": "tt",
    "SLV": "sv", "GUA": "gt",
    "BRA": "br", "ARG": "ar", "COL": "co", "URU": "uy", "ECU": "ec",
    "CHI": "cl", "BOL": "bo", "PAR": "py", "PER": "pe", "VEN": "ve",
    "FRA": "fr", "ENG": "gb-eng", "ESP": "es", "GER": "de", "POR": "pt",
    "NED": "nl", "BEL": "be", "ITA": "it", "CRO": "hr", "SUI": "ch",
    "AUT": "at", "TUR": "tr", "SCO": "gb-sct", "ALB": "al", "SRB": "rs",
    "SVN": "si", "HUN": "hu", "ROU": "ro", "SVK": "sk", "UKR": "ua",
    "CZE": "cz", "BIH": "ba", "GRE": "gr", "NOR": "no", "SWE": "se",
    "DEN": "dk", "POL": "pl",
    "JPN": "jp", "KOR": "kr", "AUS": "au", "IRN": "ir", "KSA": "sa",
    "JOR": "jo", "QAT": "qa", "IRQ": "iq", "UZB": "uz",
    "MAR": "ma", "EGY": "eg", "NGA": "ng", "CMR": "cm", "SEN": "sn",
    "CIV": "ci", "GHA": "gh", "TUN": "tn", "ALG": "dz", "RSA": "za",
    "DRC": "cd", "COD": "cd", "MLI": "ml", "CPV": "cv", "SDN": "sd",
    "NZL": "nz",
}


def _flag_url(code: str) -> str:
    iso2 = _FIFA_TO_ISO2.get(code.upper(), code[:2].lower())
    return f"https://flagcdn.com/w40/{iso2}.png"


def _ensure_teams_loaded() -> None:
    global _teams_loaded
    if not _teams_loaded:
        _reload_teams_cache()


def _reload_teams_cache() -> None:
    global _teams_loaded
    if supabase is None:
        return
    response = supabase.table("teams").select("*").execute()
    for t in response.data:
        team = _team_from_row(t)
        _teams_by_code[team.code] = team
        if t.get("id") is not None:
            _team_id_to_code[t["id"]] = team.code
    _teams_loaded = True
    logger.info("Teams cache loaded: %d teams", len(_teams_by_code))


def _reload_team(code: str) -> None:
    """Refresh a single team row in the in-memory cache from Supabase."""
    if supabase is None:
        return
    resp = supabase.table("teams").select("*").eq("code", code.upper()).execute()
    if resp.data:
        row = resp.data[0]
        team = _team_from_row(row)
        _teams_by_code[team.code] = team
        if row.get("id") is not None:
            _team_id_to_code[row["id"]] = team.code


def _require_supabase() -> None:
    if supabase is None:
        raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY in .env")


_TEAM_STATS_FIELDS = {f.alias or name for name, f in TeamStats.model_fields.items()}


def _team_from_row(t: dict) -> Team:
    raw = t["stats"] if isinstance(t["stats"], dict) else {}
    code = t["code"]
    # Strip keys that are not TeamStats fields (e.g. flag_url stored in stats JSONB)
    stats_raw = {k: v for k, v in raw.items() if k in _TEAM_STATS_FIELDS}
    return Team(
        id=t["id"],
        name=t["name"],
        code=code,
        group_letter=t["group_letter"],
        fifa_ranking=t["fifa_ranking"],
        confederation=t["confederation"],
        flag_emoji=t["flag_emoji"],
        flag_url=raw.get("flag_url") or t.get("flag_url") or _flag_url(code),
        stats=TeamStats(**stats_raw),
    )


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

def load_teams() -> list[Team]:
    _require_supabase()
    _ensure_teams_loaded()
    return list(_teams_by_code.values())


def get_team_by_code(code: str) -> Optional[Team]:
    if not code:
        return None
    _ensure_teams_loaded()
    code = code.upper()
    team = _teams_by_code.get(code)
    if team is None:
        # Self-heal: the entry may have been evicted after a stats update
        _reload_team(code)
        team = _teams_by_code.get(code)
    return team


def get_teams_by_group(letter: str) -> list[Team]:
    _ensure_teams_loaded()
    return [t for t in _teams_by_code.values() if t.group_letter == letter.upper()]


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------

def _get_team_map() -> dict[int, str]:
    _ensure_teams_loaded()
    return _team_id_to_code


def _match_from_row(m: dict, team_map: dict[int, str]) -> Match:
    return Match(
        id=m["id"],
        match_number=m["match_number"],
        stage=m["stage"],
        group_letter=m["group_letter"],
        home_team_code=team_map.get(m["home_team_id"], ""),
        away_team_code=team_map.get(m["away_team_id"], ""),
        match_date=m["match_date"],
        venue=m["venue"] or "",
        city=m["city"] or "",
        home_score=m["home_score"],
        away_score=m["away_score"],
        status=m["status"],
    )


def load_matches(
    stage: Optional[str] = None,
    group: Optional[str] = None,
    status: Optional[str] = None,
) -> list[Match]:
    _require_supabase()
    team_map = _get_team_map()
    query = supabase.table("matches").select("*")
    if stage:
        query = query.eq("stage", stage)
    if group:
        query = query.eq("group_letter", group.upper())
    if status:
        query = query.eq("status", status)
    response = query.execute()
    return [_match_from_row(m, team_map) for m in response.data]


def get_match_by_id(match_id: int) -> Optional[Match]:
    _require_supabase()
    team_map = _get_team_map()
    response = supabase.table("matches").select("*").eq("id", match_id).execute()
    if not response.data:
        response = supabase.table("matches").select("*").eq("match_number", match_id).execute()
    if response.data:
        return _match_from_row(response.data[0], team_map)
    return None


def get_upcoming_matches(limit: int = 10) -> list[Match]:
    _require_supabase()
    now = datetime.now(timezone.utc).isoformat()
    team_map = _get_team_map()
    response = (
        supabase.table("matches")
        .select("*")
        .eq("status", "scheduled")
        .gte("match_date", now)
        .order("match_date")
        .limit(limit)
        .execute()
    )
    return [_match_from_row(m, team_map) for m in response.data]


def enrich_match(match: Match) -> MatchWithTeams:
    home = get_team_by_code(match.home_team_code)
    away = get_team_by_code(match.away_team_code)
    return MatchWithTeams(
        match=match,
        home_team_name=home.name if home else match.home_team_code,
        away_team_name=away.name if away else match.away_team_code,
        home_team_flag=home.flag_emoji if home else "",
        away_team_flag=away.flag_emoji if away else "",
        home_team_flag_url=home.flag_url if home else "",
        away_team_flag_url=away.flag_url if away else "",
        home_team_ranking=home.fifa_ranking if home else 0,
        away_team_ranking=away.fifa_ranking if away else 0,
        home_team_confederation=home.confederation if home else "",
        away_team_confederation=away.confederation if away else "",
    )


def upsert_knockout_match(
    match_number: int,
    stage: str,
    home_code: str,
    away_code: str,
    match_date: str,
    venue: str = "",
    city: str = "",
) -> str:
    """
    Create or update a knockout-stage fixture (round_of_32 … final) once both
    teams are known. Keyed by match_number (group stage occupies 1..72, the 32
    knockout slots take 73..104).

    Returns "inserted" for a brand-new fixture, "updated" if the row already
    existed, or "" if either team code is unknown. Never touches an existing
    row's status / score, so a result already synced is preserved.
    """
    _require_supabase()
    _ensure_teams_loaded()
    home = _teams_by_code.get(home_code.upper())
    away = _teams_by_code.get(away_code.upper())
    if not home or not away:
        return ""

    payload = {
        "stage": stage,
        "home_team_id": home.id,
        "away_team_id": away.id,
        "match_date": match_date,
        "venue": venue,
        "city": city,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    existing = supabase.table("matches").select("id").eq("match_number", match_number).execute()
    if existing.data:
        supabase.table("matches").update(payload).eq("match_number", match_number).execute()
        return "updated"

    payload["match_number"] = match_number
    payload["status"] = "scheduled"
    payload["group_letter"] = None
    supabase.table("matches").insert(payload).execute()
    logger.info("Knockout fixture created: #%d %s %s vs %s", match_number, stage, home_code, away_code)
    return "inserted"


def update_match_result(match_id: int, home_score: int, away_score: int) -> Optional[Match]:
    _require_supabase()
    match = get_match_by_id(match_id)
    if match is None:
        return None
    supabase.table("matches").update({
        "home_score": home_score,
        "away_score": away_score,
        "status": "completed",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", match.id).execute()
    _recalculate_prediction_points(match.id, home_score, away_score)
    return get_match_by_id(match_id)


# ---------------------------------------------------------------------------
# User predictions
# ---------------------------------------------------------------------------

def save_prediction(data: MyPredictionCreate) -> MyPrediction:
    _require_supabase()
    match = get_match_by_id(data.match_id)
    db_data = {
        "match_id": data.match_id,
        "predicted_home_score": data.predicted_home_score,
        "predicted_away_score": data.predicted_away_score,
        "confidence": int(data.confidence * 100),
        "notes": data.notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if match and match.home_score is not None and match.away_score is not None:
        db_data["points_earned"] = _calculate_points(
            data.predicted_home_score, data.predicted_away_score,
            match.home_score, match.away_score,
        )
    existing = supabase.table("my_predictions").select("id").eq("match_id", data.match_id).execute()
    if existing.data:
        res = supabase.table("my_predictions").update(db_data).eq("match_id", data.match_id).execute()
    else:
        res = supabase.table("my_predictions").insert(db_data).execute()
    p = res.data[0]
    return _prediction_from_row(p)


def get_predictions() -> list[MyPrediction]:
    _require_supabase()
    response = supabase.table("my_predictions").select("*").execute()
    return [_prediction_from_row(p) for p in response.data]


def delete_prediction(prediction_id: int) -> bool:
    _require_supabase()
    res = supabase.table("my_predictions").delete().eq("id", prediction_id).execute()
    return bool(res.data)


def get_prediction_by_match(match_id: int) -> Optional[MyPrediction]:
    _require_supabase()
    response = supabase.table("my_predictions").select("*").eq("match_id", match_id).execute()
    if response.data:
        return _prediction_from_row(response.data[0])
    return None


def _prediction_from_row(p: dict) -> MyPrediction:
    return MyPrediction(
        id=p["id"],
        match_id=p["match_id"],
        predicted_home_score=p["predicted_home_score"],
        predicted_away_score=p["predicted_away_score"],
        confidence=p.get("confidence", 50) / 100.0,
        notes=p.get("notes"),
        points_earned=p.get("points_earned"),
        created_at=p.get("created_at", datetime.utcnow()),
    )


def _recalculate_prediction_points(match_id: int, home_score: int, away_score: int) -> None:
    pred = get_prediction_by_match(match_id)
    if pred:
        points = _calculate_points(
            pred.predicted_home_score, pred.predicted_away_score,
            home_score, away_score,
        )
        supabase.table("my_predictions").update({
            "points_earned": points,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("match_id", match_id).execute()


def _calculate_points(ph: int, pa: int, ah: int, aa: int) -> int:
    if ph == ah and pa == aa:
        return 3
    pred = 1 if ph > pa else (-1 if ph < pa else 0)
    actual = 1 if ah > aa else (-1 if ah < aa else 0)
    return 1 if pred == actual else 0


# ---------------------------------------------------------------------------
# AI predictions cache
# ---------------------------------------------------------------------------

def _ai_prediction_from_row(p: dict) -> AIPrediction:
    conf = float(p["confidence_score"])
    if conf > 1.0:
        conf /= 100.0
    return AIPrediction(
        match_id=p["match_id"],
        model_used=p.get("model_used") or "deepseek-chat + poisson",
        predicted_home_score=p["predicted_home_score"],
        predicted_away_score=p["predicted_away_score"],
        home_win_prob=float(p["home_win_prob"]),
        draw_prob=float(p["draw_prob"]),
        away_win_prob=float(p["away_win_prob"]),
        confidence_score=conf,
        analysis_text=p.get("analysis_text") or "",
        factors=p.get("factors") or [],
        poisson_home_lambda=float(p.get("poisson_home_lambda") or 1.2),
        poisson_away_lambda=float(p.get("poisson_away_lambda") or 1.2),
        scoreline_matrix=p.get("scoreline_matrix") or [],
    )


def get_ai_prediction(match_id: int) -> Optional[AIPrediction]:
    _require_supabase()
    response = supabase.table("ai_predictions").select("*").eq("match_id", match_id).execute()
    if not response.data:
        return None
    return _ai_prediction_from_row(response.data[0])


def get_all_ai_predictions() -> dict[int, AIPrediction]:
    """Bulk fetch of cached AI predictions, keyed by match_id (1 DB call)."""
    _require_supabase()
    response = supabase.table("ai_predictions").select("*").execute()
    preds: dict[int, AIPrediction] = {}
    for p in response.data or []:
        try:
            preds[p["match_id"]] = _ai_prediction_from_row(p)
        except Exception:
            continue
    return preds


def delete_ai_prediction(match_id: int) -> None:
    _require_supabase()
    supabase.table("ai_predictions").delete().eq("match_id", match_id).execute()


# ---------------------------------------------------------------------------
# Head-to-head records
# ---------------------------------------------------------------------------

def get_all_h2h() -> list[dict]:
    """Fetch all H2H records (used for bulk pre-fetch in simulation)."""
    _require_supabase()
    res = supabase.table("head_to_head").select("*").execute()
    return res.data or []


def get_h2h(team_a: str, team_b: str) -> Optional[dict]:
    """Get H2H record for a specific matchup (either ordering)."""
    _require_supabase()
    res = supabase.table("head_to_head").select("*").or_(
        f"and(team_a_code.eq.{team_a.upper()},team_b_code.eq.{team_b.upper()}),"
        f"and(team_a_code.eq.{team_b.upper()},team_b_code.eq.{team_a.upper()})"
    ).limit(1).execute()
    return res.data[0] if res.data else None


# ---------------------------------------------------------------------------
# Player absences
# ---------------------------------------------------------------------------

def get_all_active_absences() -> list[dict]:
    """Fetch all active absences (bulk pre-fetch for simulation)."""
    _require_supabase()
    res = supabase.table("player_absences").select("*").eq("is_active", True).execute()
    return res.data or []


def get_active_absences(team_code: str) -> list[dict]:
    """Get active absences for a single team."""
    _require_supabase()
    res = supabase.table("player_absences").select("*").eq("team_code", team_code.upper()).eq("is_active", True).execute()
    return res.data or []


def add_player_absence(
    team_code: str,
    player_name: str,
    position: Optional[str] = None,
    importance: int = 2,
    reason: str = "injury",
) -> dict:
    _require_supabase()
    res = supabase.table("player_absences").insert({
        "team_code": team_code.upper(),
        "player_name": player_name,
        "position": position,
        "importance": importance,
        "reason": reason,
        "is_active": True,
    }).execute()
    return res.data[0]


def delete_player_absence(absence_id: int) -> bool:
    _require_supabase()
    res = supabase.table("player_absences").delete().eq("id", absence_id).execute()
    return bool(res.data)


# ---------------------------------------------------------------------------
# Live-sync: ELO + form updates after real matches
# ---------------------------------------------------------------------------

def update_team_elo(code: str, new_elo: int) -> None:
    """Update a team's ELO rating in the stats JSONB column."""
    _require_supabase()
    code = code.upper()
    resp = supabase.table("teams").select("stats").eq("code", code).execute()
    if not resp.data:
        return
    stats = dict(resp.data[0]["stats"] or {})
    stats["elo_rating"] = new_elo
    supabase.table("teams").update({"stats": stats}).eq("code", code).execute()
    if code in _teams_by_code:
        _teams_by_code[code].stats.elo_rating = new_elo
    logger.info("ELO updated: %s → %d", code, new_elo)


def update_team_form_after_match(code: str, goals_for: int, goals_against: int) -> None:
    """Append a WC match result and recalculate form stats."""
    _require_supabase()
    code = code.upper()
    resp = supabase.table("teams").select("stats").eq("code", code).execute()
    if not resp.data:
        return
    stats = dict(resp.data[0]["stats"] or {})

    result = "W" if goals_for > goals_against else ("D" if goals_for == goals_against else "L")
    window: list[str] = list(stats.get("wc_results_window", []))
    window.append(result)
    window = window[-10:]

    stats["wc_results_window"] = window
    stats["wins_last_10"] = window.count("W")
    stats["draws_last_10"] = window.count("D")
    stats["losses_last_10"] = window.count("L")
    stats["form_last_5"] = window[-5:].count("W")

    total_gf = stats.get("wc_goals_for", 0) + goals_for
    total_ga = stats.get("wc_goals_against", 0) + goals_against
    n = len(window)
    stats["wc_goals_for"] = total_gf
    stats["wc_goals_against"] = total_ga
    stats["goals_scored_avg"] = round(total_gf / n, 2)
    stats["goals_conceded_avg"] = round(total_ga / n, 2)

    supabase.table("teams").update({"stats": stats}).eq("code", code).execute()
    # Reload (never evict) so the cache stays complete after stats updates
    _reload_team(code)
    logger.info("Form updated: %s result=%s window=%s", code, result, window)


def toggle_player_absence(absence_id: int, is_active: bool) -> bool:
    _require_supabase()
    res = supabase.table("player_absences").update({
        "is_active": is_active,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", absence_id).execute()
    return bool(res.data)


def save_ai_prediction(pred: AIPrediction) -> None:
    _require_supabase()
    db_data = {
        "match_id": pred.match_id,
        "model_used": pred.model_used,
        "predicted_home_score": pred.predicted_home_score,
        "predicted_away_score": pred.predicted_away_score,
        "home_win_prob": float(pred.home_win_prob),
        "draw_prob": float(pred.draw_prob),
        "away_win_prob": float(pred.away_win_prob),
        "confidence_score": float(pred.confidence_score),
        "analysis_text": pred.analysis_text,
        "factors": pred.factors,
        "poisson_home_lambda": float(pred.poisson_home_lambda),
        "poisson_away_lambda": float(pred.poisson_away_lambda),
        "scoreline_matrix": pred.scoreline_matrix,
    }
    existing = supabase.table("ai_predictions").select("id").eq("match_id", pred.match_id).execute()
    if existing.data:
        supabase.table("ai_predictions").update(db_data).eq("match_id", pred.match_id).execute()
    else:
        supabase.table("ai_predictions").insert(db_data).execute()
