"""
Predict any club or national-team match using the same Poisson + DeepSeek engine.
Usage:
  python predict_custom_match.py CPA RYO
  python predict_custom_match.py CPA RYO --city London
  python predict_custom_match.py --home "Crystal Palace" --away "Rayo Vallecano"

Built-in club profiles: CPA, RYO, MCY, ARS, BAR, RMA, ATM, LIV, CHE, TOT, MCI, MUN
Built-in national team codes (from Supabase): MEX, USA, ARG, BRA, FRA, ESP, etc.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Windows console UTF-8 fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.models.team import Team, TeamStats
from app.models.match import Match, MatchStatus
from app.services import analysis as analysis_service
from app.services import llm_service

# ---------------------------------------------------------------------------
# Built-in club profiles — edit xg / elo to reflect latest season
# ---------------------------------------------------------------------------
_CLUBS: dict[str, dict] = {
    # ── Premier League ───────────────────────────────────────────────────────
    "CPA": {
        "name": "Crystal Palace", "confederation": "UEFA", "fifa_ranking": 55,
        "flag_emoji": "🦅", "elo_rating": 1650,
        "xg_for_avg": 1.22, "xg_against_avg": 1.18,
        "wins_last_10": 5, "draws_last_10": 2, "losses_last_10": 3,
        "form_last_5": 3, "clean_sheets_last_10": 3,
        "goals_scored_avg": 1.30, "goals_conceded_avg": 1.15,
    },
    "ARS": {
        "name": "Arsenal", "confederation": "UEFA", "fifa_ranking": 5,
        "flag_emoji": "🔴", "elo_rating": 1880,
        "xg_for_avg": 2.10, "xg_against_avg": 0.85,
        "wins_last_10": 7, "draws_last_10": 2, "losses_last_10": 1,
        "form_last_5": 4, "clean_sheets_last_10": 5,
        "goals_scored_avg": 2.20, "goals_conceded_avg": 0.90,
    },
    "LIV": {
        "name": "Liverpool", "confederation": "UEFA", "fifa_ranking": 4,
        "flag_emoji": "🔴", "elo_rating": 1890,
        "xg_for_avg": 2.20, "xg_against_avg": 0.90,
        "wins_last_10": 8, "draws_last_10": 1, "losses_last_10": 1,
        "form_last_5": 4, "clean_sheets_last_10": 5,
        "goals_scored_avg": 2.30, "goals_conceded_avg": 0.85,
    },
    "MCI": {
        "name": "Manchester City", "confederation": "UEFA", "fifa_ranking": 3,
        "flag_emoji": "🔵", "elo_rating": 1920,
        "xg_for_avg": 2.25, "xg_against_avg": 0.80,
        "wins_last_10": 7, "draws_last_10": 2, "losses_last_10": 1,
        "form_last_5": 4, "clean_sheets_last_10": 6,
        "goals_scored_avg": 2.30, "goals_conceded_avg": 0.80,
    },
    "CHE": {
        "name": "Chelsea", "confederation": "UEFA", "fifa_ranking": 20,
        "flag_emoji": "🔵", "elo_rating": 1780,
        "xg_for_avg": 1.75, "xg_against_avg": 1.10,
        "wins_last_10": 6, "draws_last_10": 2, "losses_last_10": 2,
        "form_last_5": 3, "clean_sheets_last_10": 4,
        "goals_scored_avg": 1.80, "goals_conceded_avg": 1.10,
    },
    "TOT": {
        "name": "Tottenham Hotspur", "confederation": "UEFA", "fifa_ranking": 25,
        "flag_emoji": "⚪", "elo_rating": 1760,
        "xg_for_avg": 1.70, "xg_against_avg": 1.20,
        "wins_last_10": 5, "draws_last_10": 2, "losses_last_10": 3,
        "form_last_5": 3, "clean_sheets_last_10": 3,
        "goals_scored_avg": 1.70, "goals_conceded_avg": 1.25,
    },
    "MUN": {
        "name": "Manchester United", "confederation": "UEFA", "fifa_ranking": 30,
        "flag_emoji": "🔴", "elo_rating": 1740,
        "xg_for_avg": 1.50, "xg_against_avg": 1.30,
        "wins_last_10": 5, "draws_last_10": 2, "losses_last_10": 3,
        "form_last_5": 3, "clean_sheets_last_10": 3,
        "goals_scored_avg": 1.50, "goals_conceded_avg": 1.30,
    },
    # ── La Liga ──────────────────────────────────────────────────────────────
    "RYO": {
        "name": "Rayo Vallecano", "confederation": "UEFA", "fifa_ranking": 90,
        "flag_emoji": "⚡", "elo_rating": 1555,
        "xg_for_avg": 1.02, "xg_against_avg": 1.48,
        "wins_last_10": 3, "draws_last_10": 3, "losses_last_10": 4,
        "form_last_5": 2, "clean_sheets_last_10": 2,
        "goals_scored_avg": 1.00, "goals_conceded_avg": 1.45,
    },
    "BAR": {
        "name": "FC Barcelona", "confederation": "UEFA", "fifa_ranking": 2,
        "flag_emoji": "🔵🔴", "elo_rating": 1950,
        "xg_for_avg": 2.40, "xg_against_avg": 0.75,
        "wins_last_10": 8, "draws_last_10": 1, "losses_last_10": 1,
        "form_last_5": 5, "clean_sheets_last_10": 6,
        "goals_scored_avg": 2.50, "goals_conceded_avg": 0.75,
    },
    "RMA": {
        "name": "Real Madrid", "confederation": "UEFA", "fifa_ranking": 1,
        "flag_emoji": "⚪", "elo_rating": 1980,
        "xg_for_avg": 2.30, "xg_against_avg": 0.70,
        "wins_last_10": 8, "draws_last_10": 1, "losses_last_10": 1,
        "form_last_5": 5, "clean_sheets_last_10": 7,
        "goals_scored_avg": 2.40, "goals_conceded_avg": 0.70,
    },
    "ATM": {
        "name": "Atletico Madrid", "confederation": "UEFA", "fifa_ranking": 8,
        "flag_emoji": "🔴⚪", "elo_rating": 1860,
        "xg_for_avg": 1.60, "xg_against_avg": 0.85,
        "wins_last_10": 6, "draws_last_10": 3, "losses_last_10": 1,
        "form_last_5": 4, "clean_sheets_last_10": 5,
        "goals_scored_avg": 1.60, "goals_conceded_avg": 0.85,
    },
    # ── Bundesliga ────────────────────────────────────────────────────────────
    "FCB": {
        "name": "Bayern München", "confederation": "UEFA", "fifa_ranking": 3,
        "flag_emoji": "🔴", "elo_rating": 1960,
        "xg_for_avg": 2.50, "xg_against_avg": 0.85,
        "wins_last_10": 8, "draws_last_10": 1, "losses_last_10": 1,
        "form_last_5": 5, "clean_sheets_last_10": 5,
        "goals_scored_avg": 2.60, "goals_conceded_avg": 0.90,
    },
    "BVB": {
        "name": "Borussia Dortmund", "confederation": "UEFA", "fifa_ranking": 12,
        "flag_emoji": "🟡", "elo_rating": 1820,
        "xg_for_avg": 1.90, "xg_against_avg": 1.10,
        "wins_last_10": 6, "draws_last_10": 2, "losses_last_10": 2,
        "form_last_5": 3, "clean_sheets_last_10": 4,
        "goals_scored_avg": 1.95, "goals_conceded_avg": 1.15,
    },
    # ── Serie A ────────────────────────────────────────────────────────────────
    "JUV": {
        "name": "Juventus", "confederation": "UEFA", "fifa_ranking": 15,
        "flag_emoji": "⚫⚪", "elo_rating": 1830,
        "xg_for_avg": 1.55, "xg_against_avg": 0.90,
        "wins_last_10": 6, "draws_last_10": 2, "losses_last_10": 2,
        "form_last_5": 3, "clean_sheets_last_10": 5,
        "goals_scored_avg": 1.60, "goals_conceded_avg": 0.90,
    },
    "INT": {
        "name": "Inter Milan", "confederation": "UEFA", "fifa_ranking": 6,
        "flag_emoji": "🔵⚫", "elo_rating": 1900,
        "xg_for_avg": 2.00, "xg_against_avg": 0.80,
        "wins_last_10": 7, "draws_last_10": 2, "losses_last_10": 1,
        "form_last_5": 4, "clean_sheets_last_10": 6,
        "goals_scored_avg": 2.10, "goals_conceded_avg": 0.80,
    },
}


def _build_team(code: str, profile: dict) -> Team:
    return Team(
        id=None,
        name=profile["name"],
        code=code,
        group_letter="X",
        fifa_ranking=profile["fifa_ranking"],
        confederation=profile["confederation"],
        flag_emoji=profile["flag_emoji"],
        flag_url="",
        stats=TeamStats(
            goals_scored_avg=profile["goals_scored_avg"],
            goals_conceded_avg=profile["goals_conceded_avg"],
            wins_last_10=profile["wins_last_10"],
            draws_last_10=profile["draws_last_10"],
            losses_last_10=profile["losses_last_10"],
            world_cup_appearances=0,
            best_finish="N/A",
            elo_rating=profile["elo_rating"],
            xg_for_avg=profile["xg_for_avg"],
            xg_against_avg=profile["xg_against_avg"],
            clean_sheets_last_10=profile["clean_sheets_last_10"],
            form_last_5=profile["form_last_5"],
        ),
    )


def _get_team(code: str) -> Team:
    code = code.upper()
    if code in _CLUBS:
        return _build_team(code, _CLUBS[code])
    # Fall back to Supabase national teams
    from app.services import data_service
    team = data_service.get_team_by_code(code)
    if team is None:
        print(f"ERROR: Equipo '{code}' no encontrado. Códigos de clubes disponibles:")
        for c, p in _CLUBS.items():
            print(f"  {c:4s}  {p['name']}")
        sys.exit(1)
    return team


def _print_result(home: Team, away: Team, stat: dict, merged: dict) -> None:
    sw = 0.60
    lw = 0.40

    hwin = round(stat["home_win_prob"] * sw + merged.get("home_win_prob", stat["home_win_prob"]) * lw, 3)
    draw = round(stat["draw_prob"] * sw + merged.get("draw_prob", stat["draw_prob"]) * lw, 3)
    awin = round(stat["away_win_prob"] * sw + merged.get("away_win_prob", stat["away_win_prob"]) * lw, 3)
    total = hwin + draw + awin
    if total > 0:
        hwin, draw, awin = hwin / total, draw / total, awin / total

    mh = max(0, round(stat["predicted_home_score"] * sw + merged.get("predicted_home_score", stat["predicted_home_score"]) * lw))
    ma = max(0, round(stat["predicted_away_score"] * sw + merged.get("predicted_away_score", stat["predicted_away_score"]) * lw))
    conf = round(stat["confidence"] * sw + merged.get("confidence_score", stat["confidence"]) * lw, 3)

    print("\n" + "=" * 60)
    print(f"  {home.name}  vs  {away.name}")
    print("=" * 60)
    print(f"\n  Marcador predicho : {mh} - {ma}")
    print(f"  λ Poisson         : {stat['poisson_home_lambda']:.3f} - {stat['poisson_away_lambda']:.3f}")
    print(f"\n  Probabilidades    : {hwin:.0%} / {draw:.0%} / {awin:.0%}")
    print(f"  (local gana / empate / visitante gana)")
    print(f"\n  Confianza         : {conf:.0%}")
    print(f"\n  ELO               : {home.stats.elo_rating} vs {away.stats.elo_rating}  (dif: {home.stats.elo_rating - away.stats.elo_rating:+d})")
    print(f"  xG ataque/defensa : {home.stats.xg_for_avg}/{home.stats.xg_against_avg}  vs  {away.stats.xg_for_avg}/{away.stats.xg_against_avg}")

    matrix = stat.get("scoreline_matrix", [])
    if matrix:
        print("\n  Matriz de marcadores (probabilidad %):")
        header = "       " + "  ".join(f"A{a}" for a in range(len(matrix[0])))
        print("  " + header)
        for h, row in enumerate(matrix):
            cells = "  ".join(f"{v*100:4.1f}" for v in row)
            print(f"  L{h}  {cells}")

    if merged.get("analysis_text"):
        print(f"\n  Análisis DeepSeek:\n")
        for line in merged["analysis_text"].split(". "):
            if line.strip():
                print(f"    • {line.strip()}.")
    if merged.get("factors"):
        print(f"\n  Factores clave:")
        for f in merged["factors"]:
            print(f"    - {f}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Predicción Poisson + DeepSeek para cualquier partido")
    parser.add_argument("home_code", nargs="?", help="Código local (ej: CPA, ARG, BAR)")
    parser.add_argument("away_code", nargs="?", help="Código visitante (ej: RYO, BRA, RMA)")
    parser.add_argument("--home", help="Nombre equipo local (si no usa código)")
    parser.add_argument("--away", help="Nombre equipo visitante")
    parser.add_argument("--city", default="", help="Ciudad del partido (para modificadores de clima/altitud)")
    parser.add_argument("--lang", default="en", choices=["en", "es"], help="Idioma para búsqueda de noticias (default: en)")
    parser.add_argument("--no-news", action="store_true", help="Saltar la búsqueda de noticias recientes")
    parser.add_argument("--list", action="store_true", help="Listar todos los perfiles de clubes disponibles")
    args = parser.parse_args()

    if args.list:
        print("\nClubes disponibles:")
        for code, p in _CLUBS.items():
            print(f"  {code:4s}  ELO {p['elo_rating']:4d}  xG {p['xg_for_avg']:.2f}/{p['xg_against_avg']:.2f}  {p['name']}")
        print("\nUsa códigos FIFA para selecciones nacionales (MEX, ARG, FRA, etc.)")
        return

    home_code = args.home_code or (args.home[:3].upper() if args.home else None)
    away_code = args.away_code or (args.away[:3].upper() if args.away else None)

    if not home_code or not away_code:
        parser.print_help()
        return

    home = _get_team(home_code)
    away = _get_team(away_code)

    # Build a minimal Match for city/climate context
    fake_match = Match(
        id=0, match_number=1, stage="group", group_letter=None,
        home_team_code=home.code, away_team_code=away.code,
        match_date="2026-05-27T00:00:00Z",
        venue="", city=args.city,
        home_score=None, away_score=None,
        status=MatchStatus.SCHEDULED,
    )

    # Fetch news context
    news_context = ""
    if not args.no_news:
        print("Buscando noticias recientes ...")
        from fetch_news import get_team_news_context, fetch_news as _fetch_news
        news_context = get_team_news_context(
            home.code, home.name, away.code, away.name,
            lang=args.lang,
        )
        if news_context:
            print(f"  OK — contexto de noticias listo ({news_context.count(chr(10))+1} lineas)")
        else:
            print("  Sin noticias recientes — usando solo datos estadisticos")

    print(f"\nCalculando predicción: {home.name} vs {away.name} ...")
    stat = analysis_service.predict_match_statistical(home, away, fake_match)

    print("Consultando DeepSeek ...")
    llm = llm_service.predict_match(home, away, stat, fake_match, news_context=news_context)

    _print_result(home, away, stat, llm)


if __name__ == "__main__":
    main()
