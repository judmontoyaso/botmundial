"""AI prediction effectiveness — compares cached AI predictions against the
real results of already-played matches.

This powers the "Efectividad IA" dashboard section. It is recomputed on demand
(short TTL cache) so it stays current as the live sync writes new real results
every day, with no manual step needed.
"""

from __future__ import annotations

import math
from collections import defaultdict

from app.services import data_service
from app.services import predictor as predictor_service

_STAGE_LABELS = {
    "group": "Fase de Grupos",
    "round_of_32": "Dieciseisavos",
    "round_of_16": "Octavos",
    "quarterfinal": "Cuartos",
    "semifinal": "Semifinal",
    "third_place": "Tercer Lugar",
    "final": "Final",
}

_CONF_BUCKETS = [
    ("<45%", 0.0, 0.45),
    ("45-55%", 0.45, 0.55),
    ("55-65%", 0.55, 0.65),
    ("65%+", 0.65, 1.01),
]


def _outcome(h: int, a: int) -> str:
    if h > a:
        return "home"
    if a > h:
        return "away"
    return "draw"


def compute_ai_accuracy() -> dict:
    """
    Build the AI effectiveness report over every match that has both a real
    result and a cached AI prediction.

    Returns aggregate metrics + a match-by-match breakdown (most recent first).
    """
    matches = data_service.load_matches()
    ai_preds = data_service.get_all_ai_predictions()

    played = [
        m for m in matches
        if m.home_score is not None and m.away_score is not None
    ]
    played.sort(key=lambda m: str(m.match_date))

    rows: list[dict] = []
    outcome_correct = 0
    exact_correct = 0
    total_points = 0
    conf_sum = 0.0
    brier_sum = 0.0
    n = 0

    stage_stats: dict[str, dict] = {}
    conf_stats: dict[str, dict] = {
        label: {"label": label, "total": 0, "correct": 0} for label, _, _ in _CONF_BUCKETS
    }

    for m in played:
        pred = ai_preds.get(m.id)
        if pred is None:
            continue

        n += 1
        home = data_service.get_team_by_code(m.home_team_code)
        away = data_service.get_team_by_code(m.away_team_code)

        actual_o = _outcome(m.home_score, m.away_score)
        pred_o = _outcome(pred.predicted_home_score, pred.predicted_away_score)
        outcome_hit = pred_o == actual_o
        exact_hit = (
            pred.predicted_home_score == m.home_score
            and pred.predicted_away_score == m.away_score
        )
        points = predictor_service.calculate_points(
            pred.predicted_home_score, pred.predicted_away_score,
            m.home_score, m.away_score,
        )

        if outcome_hit:
            outcome_correct += 1
        if exact_hit:
            exact_correct += 1
        total_points += points
        conf_sum += pred.confidence_score

        # Brier score over the three outcome probabilities
        for label, prob in (
            ("home", pred.home_win_prob),
            ("draw", pred.draw_prob),
            ("away", pred.away_win_prob),
        ):
            brier_sum += (prob - (1.0 if actual_o == label else 0.0)) ** 2

        # Probability the model assigned to the outcome that actually happened
        prob_actual = (
            pred.home_win_prob if actual_o == "home"
            else pred.away_win_prob if actual_o == "away"
            else pred.draw_prob
        )

        stage_key = m.stage.value if hasattr(m.stage, "value") else str(m.stage)
        st = stage_stats.setdefault(
            stage_key,
            {"label": _STAGE_LABELS.get(stage_key, stage_key), "total": 0, "correct": 0},
        )
        st["total"] += 1
        if outcome_hit:
            st["correct"] += 1

        for label, lo, hi in _CONF_BUCKETS:
            if lo <= pred.confidence_score < hi:
                conf_stats[label]["total"] += 1
                if outcome_hit:
                    conf_stats[label]["correct"] += 1
                break

        rows.append({
            "match_id": m.id,
            "match_date": str(m.match_date),
            "stage": stage_key,
            "stage_label": _STAGE_LABELS.get(stage_key, stage_key),
            "group": m.group_letter,
            "home": m.home_team_code,
            "away": m.away_team_code,
            "home_name": home.name if home else m.home_team_code,
            "away_name": away.name if away else m.away_team_code,
            "home_flag_url": home.flag_url if home else "",
            "away_flag_url": away.flag_url if away else "",
            "actual_home": m.home_score,
            "actual_away": m.away_score,
            "predicted_home": pred.predicted_home_score,
            "predicted_away": pred.predicted_away_score,
            "actual_outcome": actual_o,
            "pred_outcome": pred_o,
            "home_win_prob": round(pred.home_win_prob * 100, 1),
            "draw_prob": round(pred.draw_prob * 100, 1),
            "away_win_prob": round(pred.away_win_prob * 100, 1),
            "confidence": round(pred.confidence_score * 100, 1),
            "prob_actual_outcome": round(prob_actual * 100, 1),
            "outcome_hit": outcome_hit,
            "exact_hit": exact_hit,
            "points": points,
        })

    for st in stage_stats.values():
        st["accuracy"] = round(st["correct"] / st["total"] * 100, 1) if st["total"] else None
    for cs in conf_stats.values():
        cs["accuracy"] = round(cs["correct"] / cs["total"] * 100, 1) if cs["total"] else None

    # Order the stage breakdown by the canonical tournament order
    stage_breakdown = [stage_stats[k] for k in _STAGE_LABELS if k in stage_stats]

    rows.reverse()  # most recent first

    return {
        "evaluated": n,
        "outcome_correct": outcome_correct,
        "outcome_accuracy_pct": round(outcome_correct / n * 100, 1) if n else 0.0,
        "exact_correct": exact_correct,
        "exact_accuracy_pct": round(exact_correct / n * 100, 1) if n else 0.0,
        "total_points": total_points,
        "max_points": n * 3,
        "avg_points": round(total_points / n, 2) if n else 0.0,
        "avg_confidence": round(conf_sum / n * 100, 1) if n else 0.0,
        "brier_score": round(brier_sum / n / 3, 4) if n else None,
        "stage_breakdown": stage_breakdown,
        "confidence_breakdown": list(conf_stats.values()),
        "matches": rows,
    }
