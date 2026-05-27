"""
Fetch real match statistics from ESPN public API for all WC 2026 teams.

Computes from recent international fixtures (last 10 finished matches):
  - wins_last_10, draws_last_10, losses_last_10
  - goals_scored_avg, goals_conceded_avg
  - clean_sheets_last_10
  - form_last_5 (wins in last 5 results)

Preserves existing stats:
  elo_rating, xg_for_avg, xg_against_avg, world_cup_appearances, best_finish, spi_rating

ESPN API: site.api.espn.com/apis/site/v2/sports/soccer/{league}/teams/{id}/schedule
  - Public, no authentication, no rate limits
  - Team IDs pre-mapped below; also cached in backend/cache/espn_team_ids.json
"""
import os
import sys
import json
import asyncio
from pathlib import Path

import httpx
from dotenv import load_dotenv
from supabase import create_client, Client

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == "your_supabase_url":
    print("ERROR: Configura SUPABASE_URL y SUPABASE_KEY en tu .env")
    sys.exit(1)

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
CACHE_FILE = Path(__file__).parent / "cache" / "espn_team_ids.json"

# Pre-mapped ESPN IDs for WC 2026 teams — verified from ESPN team listing endpoints
KNOWN_ESPN_IDS: dict[str, int] = {
    # CONCACAF (from concacaf.nations.league teams)
    "MEX": 203, "USA": 660, "CAN": 206, "CRC": 214, "PAN": 2659,
    "HON": 215, "JAM": 1038, "HAI": 2654, "CUW": 11678, "TRI": 2627,
    "SLV": 2650, "GUA": 2652,
    # CONMEBOL (from fifa.worldq.conmebol teams)
    "BRA": 205, "ARG": 202, "COL": 208, "URU": 212, "ECU": 209,
    "CHI": 207, "BOL": 204, "PAR": 210, "PER": 211, "VEN": 213,
    # UEFA (from uefa.nations + uefa.euro — verified)
    "FRA": 478, "ENG": 448, "ESP": 164, "GER": 481, "POR": 482,
    "NED": 449, "BEL": 459, "ITA": 162, "CRO": 477, "SUI": 475,
    "AUT": 474, "TUR": 465, "SCO": 580, "ALB": 585, "SRB": 6757,
    "SVN": 472, "HUN": 480, "ROU": 473, "SVK": 468, "UKR": 457,
    "CZE": 450, "BIH": 452, "GRE": 455, "NOR": 464, "SWE": 466,
    "DEN": 479, "POL": 471,
    # AFC (from afc.asian.cup teams — verified)
    "JPN": 627, "KOR": 451, "AUS": 628, "IRN": 469, "KSA": 655,
    "JOR": 2917, "QAT": 4398, "IRQ": 4375, "UZB": 2570,
    # CAF (from caf.nations + fifa.worldq.caf — verified)
    "MAR": 2869, "EGY": 2620, "NGA": 657, "CMR": 656, "SEN": 654,
    "CIV": 4789, "GHA": 4469, "TUN": 659, "ALG": 624, "RSA": 467,
    "DRC": 2850, "MLI": 2849, "CPV": 2597, "SDN": 4319,
    # OFC (from fifa.worldq.ofc teams — verified)
    "NZL": 2666,
}

# Competition slugs to try per confederation (ordered by most relevant first)
CONF_SLUGS: dict[str, list[str]] = {
    "CONCACAF": [
        "concacaf.nations.league",
        "fifa.worldq.concacaf",
        "concacaf.gold.cup",
        "fifa.friendly.international",
    ],
    "CONMEBOL": [
        "fifa.worldq.conmebol",
        "conmebol.copa.america",
        "fifa.friendly.international",
    ],
    "UEFA": [
        "uefa.nations",
        "fifa.worldq.uefa",
        "uefa.euro",
        "fifa.friendly.international",
    ],
    "AFC": [
        "afc.asian.cup",
        "fifa.worldq.afc",
        "fifa.friendly.international",
    ],
    "CAF": [
        "caf.afcon",
        "fifa.worldq.caf",
        "caf.nations",
        "fifa.friendly.international",
    ],
    "OFC": [
        "ofc.nations.cup",
        "fifa.worldq.ofc",
        "fifa.friendly.international",
    ],
}

# Map team code → confederation
TEAM_CONF: dict[str, str] = {
    **{c: "CONCACAF" for c in ["MEX", "USA", "CAN", "CRC", "PAN", "HON", "JAM", "HAI", "CUW", "TRI", "SLV", "GUA"]},
    **{c: "CONMEBOL" for c in ["BRA", "ARG", "COL", "URU", "ECU", "CHI", "BOL", "PAR", "PER", "VEN"]},
    **{c: "UEFA" for c in ["FRA", "ENG", "ESP", "GER", "POR", "NED", "BEL", "ITA", "CRO", "SUI", "AUT", "TUR", "SCO", "ALB", "SRB", "SVN", "HUN", "ROU", "SVK", "UKR", "CZE", "BIH", "GRE", "NOR", "SWE", "DEN", "POL"]},
    **{c: "AFC" for c in ["JPN", "KOR", "AUS", "IRN", "KSA", "JOR", "QAT", "IRQ", "UZB"]},
    **{c: "CAF" for c in ["MAR", "EGY", "NGA", "CMR", "SEN", "CIV", "GHA", "TUN", "ALG", "RSA", "DRC", "MLI", "CPV", "SDN"]},
    **{c: "OFC" for c in ["NZL"]},
}

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_cache() -> dict[str, int]:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict[str, int]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _parse_score(score_raw) -> float:
    """ESPN score field can be a plain string, number, or nested dict {value: N}."""
    if isinstance(score_raw, dict):
        return float(score_raw.get("value", 0) or 0)
    return float(score_raw or 0)


async def fetch_team_fixtures(
    client: httpx.AsyncClient, espn_id: int, conf: str
) -> list[dict]:
    """
    Fetch finished international matches for an ESPN team across relevant competition slugs.
    Returns list of {gf, ga, winner} dicts, newest first, up to 10.
    """
    slugs = CONF_SLUGS.get(conf, ["fifa.friendly.international"])
    collected: list[dict] = []

    for slug in slugs:
        if len(collected) >= 10:
            break
        try:
            resp = await client.get(
                f"{ESPN_BASE}/{slug}/teams/{espn_id}/schedule",
                timeout=15.0,
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            events = data.get("events", [])

            for event in reversed(events):  # reversed = oldest first; we want newest first later
                comps = event.get("competitions", [])
                if not comps:
                    continue
                comp = comps[0]

                if not comp.get("status", {}).get("type", {}).get("completed", False):
                    continue

                competitors = comp.get("competitors", [])
                if len(competitors) != 2:
                    continue

                team_entry = next(
                    (c for c in competitors if str(c.get("id", "")) == str(espn_id)),
                    None,
                )
                if team_entry is None:
                    continue

                opp = next(c for c in competitors if str(c.get("id", "")) != str(espn_id))

                gf = int(_parse_score(team_entry.get("score", 0)))
                ga = int(_parse_score(opp.get("score", 0)))
                winner = team_entry.get("winner")

                collected.append({"gf": gf, "ga": ga, "winner": winner})

                if len(collected) >= 10:
                    break

        except Exception as e:
            print(f"    [{slug}] error: {e}")
            continue

    return collected[:10]


def compute_stats(matches: list[dict]) -> dict:
    wins = draws = losses = 0
    goals_for = goals_against = 0
    clean_sheets = 0
    results: list[str] = []

    for m in matches:
        gf = m["gf"]
        ga = m["ga"]
        winner = m["winner"]

        goals_for += gf
        goals_against += ga
        if ga == 0:
            clean_sheets += 1

        if winner is True:
            wins += 1
            results.append("W")
        elif winner is False:
            losses += 1
            results.append("L")
        else:
            draws += 1
            results.append("D")

    played = wins + draws + losses
    if played == 0:
        return {}

    last_5 = results[-5:] if len(results) >= 5 else results
    form_last_5 = sum(1 for r in last_5 if r == "W")

    return {
        "wins_last_10": wins,
        "draws_last_10": draws,
        "losses_last_10": losses,
        "goals_scored_avg": round(goals_for / played, 2),
        "goals_conceded_avg": round(goals_against / played, 2),
        "clean_sheets_last_10": clean_sheets,
        "form_last_5": form_last_5,
    }


async def main() -> None:
    print("Iniciando descarga de estadísticas desde ESPN API (sin límite de tasa)...")

    resp = supabase.table("teams").select("id, code, name, stats, confederation").execute()
    teams: list[dict] = resp.data
    print(f"{len(teams)} equipos cargados desde Supabase.\n")

    cache = load_cache()
    # Seed cache from hardcoded IDs (skip re-discovery for known teams)
    changed = False
    for code, eid in KNOWN_ESPN_IDS.items():
        if code not in cache:
            cache[code] = eid
            changed = True
    if changed:
        save_cache(cache)

    async with httpx.AsyncClient(timeout=20.0) as client:
        updated = 0
        skipped = 0

        for i, team in enumerate(teams, start=1):
            code = team["code"]
            name = team["name"]
            existing_stats: dict = team.get("stats") or {}
            conf = team.get("confederation") or TEAM_CONF.get(code, "UEFA")
            prefix = f"[{i:2}/{len(teams)}] {name} ({code})"

            espn_id = cache.get(code)
            if espn_id is None:
                print(f"{prefix}  Sin ID ESPN — saltado (agrega a KNOWN_ESPN_IDS).")
                skipped += 1
                continue

            print(f"{prefix}  ESPN ID: {espn_id}  conf: {conf}")
            fixtures = await fetch_team_fixtures(client, espn_id, conf)

            if not fixtures:
                print(f"  Sin partidos disponibles en ESPN.")
                skipped += 1
                continue

            new_stats = compute_stats(fixtures)
            if not new_stats:
                print(f"  Sin partidos terminados.")
                skipped += 1
                continue

            print(
                f"  {new_stats['wins_last_10']}V {new_stats['draws_last_10']}E "
                f"{new_stats['losses_last_10']}D  "
                f"GF/G:{new_stats['goals_scored_avg']}  GC/G:{new_stats['goals_conceded_avg']}  "
                f"CS:{new_stats['clean_sheets_last_10']}  F5:{new_stats['form_last_5']}"
            )

            # Preserve ELO/xG/history/SPI — never overwrite
            preserve_keys = (
                "elo_rating", "xg_for_avg", "xg_against_avg",
                "world_cup_appearances", "best_finish", "spi_rating",
            )
            preserved = {k: existing_stats[k] for k in preserve_keys if k in existing_stats}
            merged = {**existing_stats, **new_stats, **preserved}

            supabase.table("teams").update({"stats": merged}).eq("code", code).execute()
            updated += 1

    save_cache(cache)
    print(f"\nCompletado: {updated} equipos actualizados  |  {skipped} saltados")
    print("ELO, xG y SPI preservados. Reinicia el backend para reflejar los cambios.")


if __name__ == "__main__":
    asyncio.run(main())
