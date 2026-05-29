"""Qatar 2022 World Cup retroactive validation of the Poisson + ELO model.

For each of the 64 matches we run predict_match_statistical() with current
team data, compare the predicted outcome (H/D/A) with the real 90-minute
result, and accumulate calibration/accuracy metrics.

Knockout rounds that went to AET or penalties use the 90-minute score for
outcome comparison — the model predicts the game result, not the final qualifier.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.services import analysis as analysis_service
from app.services import data_service

logger = logging.getLogger("app.services.backtest")

# ---------------------------------------------------------------------------
# All 64 Qatar 2022 results  (90-minute scores)
# hg = home_goals  ag = away_goals
# pens = True when match was decided by penalties
# ---------------------------------------------------------------------------

QATAR_2022_RESULTS = [
    # ── GROUP A ──────────────────────────────────────────────────────
    {"stage": "group", "group": "A", "home": "QAT", "away": "ECU", "hg": 0, "ag": 2},
    {"stage": "group", "group": "A", "home": "SEN", "away": "NED", "hg": 0, "ag": 2},
    {"stage": "group", "group": "A", "home": "QAT", "away": "SEN", "hg": 1, "ag": 3},
    {"stage": "group", "group": "A", "home": "NED", "away": "ECU", "hg": 1, "ag": 1},
    {"stage": "group", "group": "A", "home": "ECU", "away": "SEN", "hg": 1, "ag": 2},
    {"stage": "group", "group": "A", "home": "NED", "away": "QAT", "hg": 2, "ag": 0},
    # ── GROUP B ──────────────────────────────────────────────────────
    {"stage": "group", "group": "B", "home": "ENG", "away": "IRN", "hg": 6, "ag": 2},
    {"stage": "group", "group": "B", "home": "USA", "away": "WAL", "hg": 1, "ag": 1},
    {"stage": "group", "group": "B", "home": "WAL", "away": "IRN", "hg": 0, "ag": 2},
    {"stage": "group", "group": "B", "home": "ENG", "away": "USA", "hg": 0, "ag": 0},
    {"stage": "group", "group": "B", "home": "WAL", "away": "ENG", "hg": 0, "ag": 3},
    {"stage": "group", "group": "B", "home": "IRN", "away": "USA", "hg": 0, "ag": 1},
    # ── GROUP C ──────────────────────────────────────────────────────
    {"stage": "group", "group": "C", "home": "ARG", "away": "KSA", "hg": 1, "ag": 2},
    {"stage": "group", "group": "C", "home": "POL", "away": "MEX", "hg": 0, "ag": 0},
    {"stage": "group", "group": "C", "home": "POL", "away": "ARG", "hg": 0, "ag": 2},
    {"stage": "group", "group": "C", "home": "KSA", "away": "MEX", "hg": 1, "ag": 2},
    {"stage": "group", "group": "C", "home": "POL", "away": "KSA", "hg": 2, "ag": 0},
    {"stage": "group", "group": "C", "home": "ARG", "away": "MEX", "hg": 2, "ag": 0},
    # ── GROUP D ──────────────────────────────────────────────────────
    {"stage": "group", "group": "D", "home": "DEN", "away": "TUN", "hg": 0, "ag": 0},
    {"stage": "group", "group": "D", "home": "FRA", "away": "AUS", "hg": 4, "ag": 1},
    {"stage": "group", "group": "D", "home": "TUN", "away": "AUS", "hg": 0, "ag": 1},
    {"stage": "group", "group": "D", "home": "FRA", "away": "DEN", "hg": 2, "ag": 1},
    {"stage": "group", "group": "D", "home": "AUS", "away": "DEN", "hg": 1, "ag": 0},
    {"stage": "group", "group": "D", "home": "TUN", "away": "FRA", "hg": 1, "ag": 0},
    # ── GROUP E ──────────────────────────────────────────────────────
    {"stage": "group", "group": "E", "home": "GER", "away": "JPN", "hg": 1, "ag": 2},
    {"stage": "group", "group": "E", "home": "ESP", "away": "CRC", "hg": 7, "ag": 0},
    {"stage": "group", "group": "E", "home": "JPN", "away": "CRC", "hg": 0, "ag": 1},
    {"stage": "group", "group": "E", "home": "ESP", "away": "GER", "hg": 1, "ag": 1},
    {"stage": "group", "group": "E", "home": "JPN", "away": "ESP", "hg": 2, "ag": 1},
    {"stage": "group", "group": "E", "home": "CRC", "away": "GER", "hg": 2, "ag": 4},
    # ── GROUP F ──────────────────────────────────────────────────────
    {"stage": "group", "group": "F", "home": "MAR", "away": "CRO", "hg": 0, "ag": 0},
    {"stage": "group", "group": "F", "home": "BEL", "away": "CAN", "hg": 1, "ag": 0},
    {"stage": "group", "group": "F", "home": "BEL", "away": "MAR", "hg": 0, "ag": 2},
    {"stage": "group", "group": "F", "home": "CRO", "away": "CAN", "hg": 4, "ag": 1},
    {"stage": "group", "group": "F", "home": "CRO", "away": "BEL", "hg": 0, "ag": 0},
    {"stage": "group", "group": "F", "home": "CAN", "away": "MAR", "hg": 1, "ag": 2},
    # ── GROUP G ──────────────────────────────────────────────────────
    {"stage": "group", "group": "G", "home": "BRA", "away": "SRB", "hg": 2, "ag": 0},
    {"stage": "group", "group": "G", "home": "SUI", "away": "CMR", "hg": 1, "ag": 0},
    {"stage": "group", "group": "G", "home": "CMR", "away": "SRB", "hg": 3, "ag": 3},
    {"stage": "group", "group": "G", "home": "BRA", "away": "SUI", "hg": 1, "ag": 0},
    {"stage": "group", "group": "G", "home": "SRB", "away": "SUI", "hg": 2, "ag": 3},
    {"stage": "group", "group": "G", "home": "CMR", "away": "BRA", "hg": 1, "ag": 0},
    # ── GROUP H ──────────────────────────────────────────────────────
    {"stage": "group", "group": "H", "home": "URU", "away": "KOR", "hg": 0, "ag": 0},
    {"stage": "group", "group": "H", "home": "POR", "away": "GHA", "hg": 3, "ag": 2},
    {"stage": "group", "group": "H", "home": "KOR", "away": "GHA", "hg": 2, "ag": 3},
    {"stage": "group", "group": "H", "home": "POR", "away": "URU", "hg": 2, "ag": 0},
    {"stage": "group", "group": "H", "home": "KOR", "away": "POR", "hg": 2, "ag": 1},
    {"stage": "group", "group": "H", "home": "GHA", "away": "URU", "hg": 0, "ag": 2},
    # ── ROUND OF 16 ──────────────────────────────────────────────────
    {"stage": "r16", "home": "NED", "away": "USA", "hg": 3, "ag": 1},
    {"stage": "r16", "home": "ARG", "away": "AUS", "hg": 2, "ag": 1},
    {"stage": "r16", "home": "FRA", "away": "POL", "hg": 3, "ag": 1},
    {"stage": "r16", "home": "ENG", "away": "SEN", "hg": 3, "ag": 0},
    {"stage": "r16", "home": "JPN", "away": "CRO", "hg": 1, "ag": 1, "pens": True, "pen_home": 1, "pen_away": 3},
    {"stage": "r16", "home": "BRA", "away": "KOR", "hg": 4, "ag": 1},
    {"stage": "r16", "home": "MAR", "away": "ESP", "hg": 0, "ag": 0, "pens": True, "pen_home": 3, "pen_away": 0},
    {"stage": "r16", "home": "POR", "away": "SUI", "hg": 6, "ag": 1},
    # ── QUARTER-FINALS ───────────────────────────────────────────────
    {"stage": "qf", "home": "CRO", "away": "BRA", "hg": 1, "ag": 1, "pens": True, "pen_home": 4, "pen_away": 2},
    {"stage": "qf", "home": "NED", "away": "ARG", "hg": 2, "ag": 2, "pens": True, "pen_home": 3, "pen_away": 4},
    {"stage": "qf", "home": "MAR", "away": "POR", "hg": 1, "ag": 0},
    {"stage": "qf", "home": "FRA", "away": "ENG", "hg": 2, "ag": 1},
    # ── SEMI-FINALS ──────────────────────────────────────────────────
    {"stage": "sf", "home": "ARG", "away": "CRO", "hg": 3, "ag": 0},
    {"stage": "sf", "home": "FRA", "away": "MAR", "hg": 2, "ag": 0},
    # ── THIRD PLACE ──────────────────────────────────────────────────
    {"stage": "3rd", "home": "CRO", "away": "MAR", "hg": 2, "ag": 1},
    # ── FINAL ────────────────────────────────────────────────────────
    {"stage": "final", "home": "ARG", "away": "FRA", "hg": 3, "ag": 3, "pens": True, "pen_home": 4, "pen_away": 2},
]

_STAGE_LABELS = {
    "group": "Fase de Grupos",
    "r16":   "Octavos de Final",
    "qf":    "Cuartos de Final",
    "sf":    "Semifinal",
    "3rd":   "Tercer Lugar",
    "final": "Final",
}


def _actual_outcome(hg: int, ag: int) -> str:
    if hg > ag:  return "home"
    if ag > hg:  return "away"
    return "draw"


def _predicted_outcome(hw: float, dw: float, aw: float) -> str:
    if hw >= dw and hw >= aw:  return "home"
    if aw >= hw and aw >= dw:  return "away"
    return "draw"


def run_qatar_2022_backtest() -> dict:
    """
    Runs predict_match_statistical() for each of the 64 Qatar 2022 matches
    using current team data from the database.

    Returns a dict with match-by-match results and aggregate metrics.
    """
    results = []
    correct = 0
    total = 0
    skipped = 0
    skipped_teams: set[str] = set()
    prob_sum_correct = 0.0      # Brier-style calibration

    for idx, m in enumerate(QATAR_2022_RESULTS, start=1):
        home_code = m["home"]
        away_code = m["away"]

        home_team = data_service.get_team_by_code(home_code)
        away_team = data_service.get_team_by_code(away_code)

        entry: dict = {
            "idx": idx,
            "stage": m["stage"],
            "stage_label": _STAGE_LABELS.get(m["stage"], m["stage"]),
            "group": m.get("group"),
            "home": home_code,
            "away": away_code,
            "actual_hg": m["hg"],
            "actual_ag": m["ag"],
            "went_to_pens": m.get("pens", False),
            "actual_outcome": _actual_outcome(m["hg"], m["ag"]),
        }

        if home_team is None or away_team is None:
            missing = [c for c, t in [(home_code, home_team), (away_code, away_team)] if t is None]
            skipped += 1
            skipped_teams.update(missing)
            entry["status"] = "skipped"
            entry["skipped_reason"] = f"Equipo no encontrado en DB: {', '.join(missing)}"
            results.append(entry)
            continue

        try:
            pred = analysis_service.predict_match_statistical(home_team, away_team)
        except Exception as exc:
            logger.warning("Prediction failed for match %d: %s", idx, exc)
            skipped += 1
            entry["status"] = "error"
            entry["skipped_reason"] = str(exc)
            results.append(entry)
            continue

        hw = pred["home_win_prob"]
        dw = pred["draw_prob"]
        aw = pred["away_win_prob"]
        pred_outcome = _predicted_outcome(hw, dw, aw)
        actual_outcome = entry["actual_outcome"]
        hit = pred_outcome == actual_outcome

        # Probability assigned to the actual outcome
        prob_actual = hw if actual_outcome == "home" else (aw if actual_outcome == "away" else dw)
        prob_sum_correct += prob_actual

        if hit:
            correct += 1
        total += 1

        entry.update({
            "status": "ok",
            "predicted_hg": pred["predicted_home_score"],
            "predicted_ag": pred["predicted_away_score"],
            "pred_outcome": pred_outcome,
            "home_win_prob": round(hw * 100, 1),
            "draw_prob": round(dw * 100, 1),
            "away_win_prob": round(aw * 100, 1),
            "confidence": round(pred["confidence"] * 100, 1),
            "prob_actual_outcome": round(prob_actual * 100, 1),
            "hit": hit,
            "home_elo": pred["home_elo"],
            "away_elo": pred["away_elo"],
        })
        results.append(entry)

    # Aggregate metrics
    accuracy = round(correct / total * 100, 1) if total > 0 else 0.0
    avg_prob_correct = round(prob_sum_correct / total * 100, 1) if total > 0 else 0.0

    # Biggest upsets model got wrong (predicted wrong favourite by large margin)
    upsets = [
        r for r in results
        if r.get("status") == "ok" and not r["hit"]
        and abs(r.get("home_win_prob", 0) - r.get("away_win_prob", 0)) > 20
    ]
    upsets.sort(key=lambda r: abs(r.get("home_win_prob", 0) - r.get("away_win_prob", 0)), reverse=True)

    # Per-stage breakdown
    stage_stats: dict[str, dict] = {}
    for r in results:
        s = r["stage"]
        if s not in stage_stats:
            stage_stats[s] = {"label": _STAGE_LABELS.get(s, s), "total": 0, "correct": 0, "skipped": 0}
        if r["status"] == "ok":
            stage_stats[s]["total"] += 1
            if r["hit"]:
                stage_stats[s]["correct"] += 1
        elif r["status"] == "skipped":
            stage_stats[s]["skipped"] += 1

    for v in stage_stats.values():
        v["accuracy"] = round(v["correct"] / v["total"] * 100, 1) if v["total"] > 0 else None

    return {
        "total_matches": len(QATAR_2022_RESULTS),
        "processed": total,
        "skipped": skipped,
        "skipped_teams": sorted(skipped_teams),
        "correct_outcomes": correct,
        "accuracy_pct": accuracy,
        "avg_prob_actual_outcome": avg_prob_correct,
        "stage_breakdown": list(stage_stats.values()),
        "matches": results,
        "top_upsets_missed": upsets[:5],
    }
