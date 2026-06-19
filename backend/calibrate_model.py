"""
Calibración del modelo Poisson+ELO usando Qatar 2022 como conjunto de validación.

Hace grid search sobre los parámetros clave de analysis.py y reporta:
  - Accuracy (% de resultados H/D/A correctos)
  - Brier Score (error cuadrático medio de probabilidades, menor = mejor)
  - Log-loss (calibración de confianza, menor = mejor)
  - Curva de calibración ASCII

Uso (desde el directorio backend/):
  python calibrate_model.py

Requiere: SUPABASE_URL y SUPABASE_KEY en .env
"""

from __future__ import annotations

import math
import os
import sys
import itertools
from collections import defaultdict
from typing import Optional

# Añadir el path del backend
sys.path.insert(0, os.path.dirname(__file__))

# Cargar .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services import data_service
from app.services.backtest import QATAR_2022_RESULTS
from app.models.team import Team

# ---------------------------------------------------------------------------
# Constantes base (valores actuales del modelo)
# ---------------------------------------------------------------------------

MEAN_XG_FOR    = 1.30
MEAN_XG_AGAINST = 1.10
MEAN_GOALS     = 1.20
DC_RHO         = -0.10  # Dixon-Coles low-score correction
DRAW_BOOST     = 1.35   # must match analysis._DRAW_BOOST so calibration reflects the real model

# ---------------------------------------------------------------------------
# Funciones Poisson (auto-contenidas, no dependen de módulos del modelo)
# ---------------------------------------------------------------------------

def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0 or k < 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def _build_matrix(lh: float, la: float, max_g: int = 5) -> list[list[float]]:
    n = max_g + 1
    m = [[_poisson_pmf(h, lh) * _poisson_pmf(a, la) for a in range(n)] for h in range(n)]
    rho = DC_RHO
    m[0][0] *= max(0.0, 1 - lh * la * rho)
    m[1][0] *= max(0.0, 1 + la * rho)
    m[0][1] *= max(0.0, 1 + lh * rho)
    m[1][1] *= max(0.0, 1 - rho)
    # Draw boost on equal-score cells (matches analysis.build_scoreline_matrix)
    for g in range(n):
        m[g][g] *= DRAW_BOOST
    total = sum(m[h][a] for h in range(n) for a in range(n))
    if total > 0:
        m = [[m[h][a] / total for a in range(n)] for h in range(n)]
    return m


def _outcome_probs(m: list[list[float]]) -> tuple[float, float, float]:
    n = len(m)
    hw = sum(m[h][a] for h in range(n) for a in range(n) if h > a)
    dr = sum(m[h][h] for h in range(n))
    aw = sum(m[h][a] for h in range(n) for a in range(n) if a > h)
    t = hw + dr + aw
    return (hw/t, dr/t, aw/t) if t > 0 else (1/3, 1/3, 1/3)


# ---------------------------------------------------------------------------
# Lambda computation con parámetros inyectables
# ---------------------------------------------------------------------------

def _form_mod(team: Team) -> float:
    return (team.stats.form_last_5 - 2.5) / 25.0


def _cont_adv(team: Team) -> float:
    c = team.confederation.upper()
    if c == "CONCACAF": return 0.12
    if c == "CONMEBOL": return 0.07
    return 0.0


def compute_lambdas(
    home: Team,
    away: Team,
    home_factor: float,
    elo_scale: float,
    form_weight: float,
    use_continent: bool,
) -> tuple[float, float]:
    ha = home.stats.xg_for_avg  / MEAN_XG_FOR
    hd = home.stats.xg_against_avg / MEAN_XG_AGAINST
    aa = away.stats.xg_for_avg  / MEAN_XG_FOR
    ad = away.stats.xg_against_avg / MEAN_XG_AGAINST

    lh = ha * ad * MEAN_GOALS * home_factor
    la = aa * hd * MEAN_GOALS

    # Continent advantage (opcional)
    if use_continent:
        lh *= (1.0 + _cont_adv(home))
        la *= (1.0 + _cont_adv(away))

    # ELO
    diff = home.stats.elo_rating - away.stats.elo_rating
    ef_h = 1.0 + diff / elo_scale
    ef_a = 1.0 - diff / elo_scale
    lh = max(0.3, lh * ef_h)
    la = max(0.3, la * ef_a)

    # Forma reciente
    lh = max(0.3, lh * (1.0 + _form_mod(home) * form_weight))
    la = max(0.3, la * (1.0 + _form_mod(away) * form_weight))

    return lh, la


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------

def brier_score(predictions: list[dict]) -> float:
    """Mean squared error of outcome probabilities."""
    total = 0.0
    for p in predictions:
        o = p["actual"]
        hw, dw, aw = p["hw"], p["dw"], p["aw"]
        total += (hw - (1 if o == "home" else 0))**2
        total += (dw - (1 if o == "draw" else 0))**2
        total += (aw - (1 if o == "away" else 0))**2
    return total / len(predictions) / 3


def log_loss(predictions: list[dict]) -> float:
    """Negative log likelihood of actual outcomes."""
    eps = 1e-9
    total = 0.0
    for p in predictions:
        o = p["actual"]
        prob = p["hw"] if o == "home" else (p["aw"] if o == "away" else p["dw"])
        total += -math.log(max(prob, eps))
    return total / len(predictions)


def accuracy(predictions: list[dict]) -> float:
    correct = sum(
        1 for p in predictions
        if p["predicted"] == p["actual"]
    )
    return correct / len(predictions)


def _predicted(hw: float, dw: float, aw: float) -> str:
    if hw >= dw and hw >= aw: return "home"
    if aw >= hw and aw >= dw: return "away"
    return "draw"


def _actual(hg: int, ag: int) -> str:
    if hg > ag: return "home"
    if ag > hg: return "away"
    return "draw"


# ---------------------------------------------------------------------------
# Evaluación de un conjunto de parámetros
# ---------------------------------------------------------------------------

def evaluate(
    teams: dict[str, Team],
    home_factor: float,
    elo_scale: float,
    form_weight: float,
    use_continent: bool,
) -> Optional[dict]:
    predictions = []
    skipped = 0

    for m in QATAR_2022_RESULTS:
        home = teams.get(m["home"])
        away = teams.get(m["away"])
        if not home or not away:
            skipped += 1
            continue

        lh, la = compute_lambdas(home, away, home_factor, elo_scale, form_weight, use_continent)
        mat = _build_matrix(lh, la)
        hw, dw, aw = _outcome_probs(mat)
        pred = _predicted(hw, dw, aw)
        act  = _actual(m["hg"], m["ag"])

        predictions.append({"hw": hw, "dw": dw, "aw": aw, "predicted": pred, "actual": act})

    if not predictions:
        return None

    return {
        "accuracy":    round(accuracy(predictions) * 100, 2),
        "brier":       round(brier_score(predictions), 4),
        "log_loss":    round(log_loss(predictions), 4),
        "n":           len(predictions),
        "skipped":     skipped,
        "predictions": predictions,
    }


# ---------------------------------------------------------------------------
# Calibration curve (ASCII)
# ---------------------------------------------------------------------------

def calibration_curve(predictions: list[dict], bins: int = 5) -> None:
    """Prints an ASCII calibration curve: predicted confidence vs actual frequency."""
    bin_size = 1.0 / bins
    buckets: dict[int, list] = defaultdict(list)

    for p in predictions:
        o = p["actual"]
        # Usamos la probabilidad del outcome predicho como "confianza"
        conf = max(p["hw"], p["dw"], p["aw"])
        hit = 1 if p["predicted"] == o else 0
        b = min(int(conf / bin_size), bins - 1)
        buckets[b].append((conf, hit))

    print("\n  Curva de calibración (confianza predicha vs tasa real de acierto):")
    print("  " + "─" * 52)
    print(f"  {'Confianza':>12}  {'N':>4}  {'% Acierto':>10}  Barra")
    print("  " + "─" * 52)
    for b in range(bins):
        data = buckets[b]
        if not data:
            continue
        lo = b * bin_size * 100
        hi = (b + 1) * bin_size * 100
        n = len(data)
        hit_rate = sum(h for _, h in data) / n * 100
        avg_conf = sum(c for c, _ in data) / n * 100
        bar_len = int(hit_rate / 5)
        bar = "█" * bar_len
        print(f"  {lo:>5.0f}–{hi:<5.0f}%  {n:>4}  {hit_rate:>8.1f}%  {bar}")
    print("  " + "─" * 52)
    print("  Ideal: cada fila debería mostrar hit_rate ≈ punto medio del rango\n")


# ---------------------------------------------------------------------------
# Grid search
# ---------------------------------------------------------------------------

def run_grid_search(teams: dict[str, Team]) -> None:
    # Parámetros a explorar
    home_factors  = [1.00, 1.04, 1.08, 1.12, 1.16]
    elo_scales    = [2000, 2500, 3000, 3500, 4000]
    form_weights  = [0.5, 1.0, 1.5]
    cont_options  = [True, False]

    total = len(home_factors) * len(elo_scales) * len(form_weights) * len(cont_options)
    print(f"\n  Grid search: {total} combinaciones de parámetros...\n")

    best_acc   = {"accuracy": 0}
    best_brier = {"brier": 9999}
    results    = []

    for hf, es, fw, co in itertools.product(home_factors, elo_scales, form_weights, cont_options):
        r = evaluate(teams, hf, es, fw, co)
        if r is None:
            continue
        r.update({"home_factor": hf, "elo_scale": es, "form_weight": fw, "continent": co})
        results.append(r)
        if r["accuracy"] > best_acc["accuracy"]:
            best_acc = r
        if r["brier"] < best_brier["brier"]:
            best_brier = r

    # Top 10 por accuracy
    top_acc = sorted(results, key=lambda x: -x["accuracy"])[:10]

    print("  ── Top 10 por Accuracy ──────────────────────────────────────────")
    print(f"  {'HF':>5}  {'ELO_S':>6}  {'FW':>5}  {'Cont':>5}  {'Acc%':>7}  {'Brier':>7}  {'LogL':>7}  {'N':>4}")
    print("  " + "─" * 60)
    for r in top_acc:
        print(
            f"  {r['home_factor']:>5.2f}  {r['elo_scale']:>6}  {r['form_weight']:>5.1f}"
            f"  {'Sí' if r['continent'] else 'No':>5}"
            f"  {r['accuracy']:>6.1f}%  {r['brier']:>7.4f}  {r['log_loss']:>7.4f}  {r['n']:>4}"
        )

    print()
    return best_acc, best_brier, top_acc


# ---------------------------------------------------------------------------
# Análisis de errores por tipo
# ---------------------------------------------------------------------------

def error_analysis(predictions: list[dict]) -> None:
    cats = {"home": {"correct": 0, "total": 0}, "draw": {"correct": 0, "total": 0}, "away": {"correct": 0, "total": 0}}
    for p in predictions:
        cats[p["actual"]]["total"] += 1
        if p["predicted"] == p["actual"]:
            cats[p["actual"]]["correct"] += 1

    print("  ── Precisión por tipo de resultado ─────────────────────────────")
    for outcome, data in cats.items():
        n = data["total"]
        c = data["correct"]
        pct = c/n*100 if n > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"  {outcome.capitalize():<10} {c:>2}/{n:<2}  {pct:>5.1f}%  {bar}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Calibración del modelo Poisson+ELO — Qatar 2022")
    print("="*60)

    # Cargar equipos desde DB
    print("\n  Cargando equipos desde Supabase...")
    all_teams_list = data_service.load_teams()
    teams = {t.code: t for t in all_teams_list}
    print(f"  {len(teams)} equipos cargados.")

    # Evaluar parámetros actuales primero
    print("\n  ── Parámetros actuales del modelo ───────────────────────────────")
    current = evaluate(teams, home_factor=1.08, elo_scale=3000, form_weight=1.0, use_continent=True)
    if current:
        print(f"  HOME_FACTOR=1.08  ELO_SCALE=3000  form_weight=1.0  continent=Sí")
        print(f"  Accuracy : {current['accuracy']}%  ({current['n']} partidos, {current['skipped']} omitidos)")
        print(f"  Brier    : {current['brier']}")
        print(f"  Log-loss : {current['log_loss']}")
        error_analysis(current["predictions"])
        calibration_curve(current["predictions"])

    # Grid search
    best_acc, best_brier, top_acc = run_grid_search(teams)

    # Comparativa
    print("\n  ── Mejores parámetros encontrados ───────────────────────────────")
    print(f"\n  Por Accuracy ({best_acc['accuracy']}%):")
    print(f"    HOME_FACTOR  = {best_acc['home_factor']}")
    print(f"    ELO_SCALE    = {best_acc['elo_scale']}")
    print(f"    form_weight  = {best_acc['form_weight']}")
    print(f"    continent    = {'Sí' if best_acc['continent'] else 'No'}")
    print(f"    Brier        = {best_acc['brier']}")

    print(f"\n  Por Brier Score ({best_brier['brier']}):")
    print(f"    HOME_FACTOR  = {best_brier['home_factor']}")
    print(f"    ELO_SCALE    = {best_brier['elo_scale']}")
    print(f"    form_weight  = {best_brier['form_weight']}")
    print(f"    continent    = {'Sí' if best_brier['continent'] else 'No'}")
    print(f"    Accuracy     = {best_brier['accuracy']}%")

    if current:
        print(f"\n  ── Ganancia vs. parámetros actuales ─────────────────────────────")
        acc_gain = best_acc['accuracy'] - current['accuracy']
        brier_gain = current['brier'] - best_brier['brier']
        print(f"  Accuracy: {current['accuracy']}% → {best_acc['accuracy']}%  ({acc_gain:+.1f}pp)")
        print(f"  Brier:    {current['brier']} → {best_brier['brier']}  ({-brier_gain:+.4f})")

    print(f"\n  ── Para aplicar el mejor resultado, editar analysis.py ──────────")
    print(f"    _HOME_FACTOR = {best_acc['home_factor']}")
    print(f"    _ELO_SCALE   = {best_acc['elo_scale']}")
    print()
    print("="*60 + "\n")
