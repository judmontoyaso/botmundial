"""
Análisis: Türk Telekom vs Anadolu Efes — BSL (Basketbol Süper Ligi)
Fuente: API-Sports Basketball (https://v1.basketball.api-sports.io)

Uso:
  python bsk_analisis.py                        # sin clave → modo scraping
  python bsk_analisis.py --key TU_API_KEY       # con clave de API-Sports
"""

import sys
import json
import argparse
import requests
from datetime import datetime

# ── Configuración ────────────────────────────────────────────────────────────

TEAM_A = "Turk Telekom"
TEAM_B = "Anadolu Efes"
BSL_LEAGUE_ID = 8       # Turkish BSL en API-Sports
SEASON = "2025-2026"

HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

def api_get(path: str, params: dict, key: str) -> dict:
    url = f"https://v1.basketball.api-sports.io{path}"
    headers = {**HEADERS_BASE, "x-apisports-key": key}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


# ── Sofascore fallback (sin clave) ───────────────────────────────────────────

SOFASCORE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.sofascore.com/",
}

TEAM_IDS_SOFASCORE = {
    "Turk Telekom":  1973,   # ID aproximado — puede cambiar
    "Anadolu Efes":  1964,
}

def sofascore_team_stats(team_id: int, team_name: str) -> dict:
    print(f"\n[Sofascore] Buscando stats de {team_name}...")
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/statistics/season/basketball"
    try:
        r = requests.get(url, headers=SOFASCORE_HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  Error: {e}")

    # búsqueda por nombre
    url2 = f"https://api.sofascore.com/api/v1/search/teams?query={requests.utils.quote(team_name)}&sport=basketball"
    try:
        r2 = requests.get(url2, headers=SOFASCORE_HEADERS, timeout=15)
        if r2.status_code == 200:
            data = r2.json()
            teams = data.get("teams", [])
            if teams:
                found = teams[0]
                print(f"  Encontrado: {found.get('name')} (ID: {found.get('id')})")
                return {"team_info": found}
    except Exception as e:
        print(f"  Error búsqueda: {e}")
    return {}


def sofascore_last_games(team_id: int, team_name: str, n: int = 5) -> list:
    print(f"[Sofascore] Últimos {n} partidos de {team_name}...")
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0"
    try:
        r = requests.get(url, headers=SOFASCORE_HEADERS, timeout=15)
        if r.status_code == 200:
            events = r.json().get("events", [])
            return events[:n]
    except Exception as e:
        print(f"  Error: {e}")
    return []


def sofascore_h2h(team_id_a: int, team_id_b: int) -> list:
    print(f"[Sofascore] Head-to-head...")
    url = f"https://api.sofascore.com/api/v1/team/{team_id_a}/team/{team_id_b}/h2h/events"
    try:
        r = requests.get(url, headers=SOFASCORE_HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json().get("events", [])[:8]
    except Exception as e:
        print(f"  Error: {e}")
    return []


# ── Modo API-Sports ──────────────────────────────────────────────────────────

def run_api_sports(key: str):
    print(f"\n{'='*60}")
    print(f"  Türk Telekom vs Anadolu Efes — BSL {SEASON}")
    print(f"  Fuente: API-Sports Basketball")
    print(f"{'='*60}\n")

    # Buscar equipos
    for name in [TEAM_A, TEAM_B]:
        print(f"── Buscando equipo: {name}")
        data = api_get("/teams", {"name": name, "league": BSL_LEAGUE_ID, "season": SEASON}, key)
        teams = data.get("response", [])
        if not teams:
            print(f"  ⚠ No encontrado. Intentando sin filtro de liga...")
            data = api_get("/teams", {"name": name}, key)
            teams = data.get("response", [])
        for t in teams[:2]:
            print(f"  → ID: {t['id']}  Nombre: {t['name']}  País: {t.get('country', {}).get('name','?')}")
        print()

    # Standings BSL
    print("── Clasificación BSL actual")
    data = api_get("/standings", {"league": BSL_LEAGUE_ID, "season": SEASON}, key)
    standings = data.get("response", [])
    for group in standings[:1]:
        for team in group.get("standings", [[]]):
            for entry in team[:10]:
                t = entry.get("team", {})
                g = entry.get("games", {})
                print(f"  {entry.get('position','?'):>2}. {t.get('name','?'):<25} "
                      f"V:{g.get('win',{}).get('total','?')}  "
                      f"D:{g.get('lose',{}).get('total','?')}")
    print()

    # Últimos partidos por equipo
    for name in [TEAM_A, TEAM_B]:
        print(f"── Últimos 5 partidos: {name}")
        data = api_get("/games", {"team": name, "league": BSL_LEAGUE_ID, "season": SEASON}, key)
        games = sorted(data.get("response", []), key=lambda g: g.get("date",""), reverse=True)[:5]
        for g in games:
            ht = g.get("teams", {}).get("home", {})
            at = g.get("teams", {}).get("away", {})
            hs = g.get("scores", {}).get("home", {}).get("total", "?")
            as_ = g.get("scores", {}).get("away", {}).get("total", "?")
            date = g.get("date", "")[:10]
            print(f"  {date}  {ht.get('name','?'):<22} {hs:>3} – {as_:<3} {at.get('name','?')}")
        print()

    # H2H directo
    print(f"── Head-to-head reciente: {TEAM_A} vs {TEAM_B}")
    data = api_get("/games", {"h2h": f"{TEAM_A}-{TEAM_B}", "season": SEASON}, key)
    games = data.get("response", [])
    for g in games[:8]:
        ht = g.get("teams", {}).get("home", {})
        at = g.get("teams", {}).get("away", {})
        hs = g.get("scores", {}).get("home", {}).get("total", "?")
        as_ = g.get("scores", {}).get("away", {}).get("total", "?")
        date = g.get("date", "")[:10]
        print(f"  {date}  {ht.get('name','?'):<22} {hs:>3} – {as_:<3} {at.get('name','?')}")
    print()


# ── Modo Sofascore (sin clave) ───────────────────────────────────────────────

def format_game_sofascore(ev: dict, my_team_id: int) -> str:
    ht = ev.get("homeTeam", {})
    at = ev.get("awayTeam", {})
    hs = ev.get("homeScore", {}).get("current", "?")
    as_ = ev.get("awayScore", {}).get("current", "?")
    ts = ev.get("startTimestamp", 0)
    date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "?"
    result = ""
    if isinstance(hs, int) and isinstance(as_, int):
        if ht.get("id") == my_team_id:
            result = "W" if hs > as_ else "L"
        else:
            result = "W" if as_ > hs else "L"
    return f"  {date}  {ht.get('name','?'):<22} {hs:>3} – {as_:<3} {at.get('name','?')}  {result}"


def run_sofascore():
    print(f"\n{'='*60}")
    print(f"  Türk Telekom vs Anadolu Efes — BSL")
    print(f"  Fuente: Sofascore (modo sin clave API)")
    print(f"{'='*60}\n")

    id_a = TEAM_IDS_SOFASCORE[TEAM_A]
    id_b = TEAM_IDS_SOFASCORE[TEAM_B]

    # Stats
    for name, tid in [(TEAM_A, id_a), (TEAM_B, id_b)]:
        print(f"── Stats de temporada: {name}")
        stats = sofascore_team_stats(tid, name)
        if stats:
            # Intentar mostrar stats relevantes
            team_stats = stats.get("statistics", stats.get("team_info", {}))
            if isinstance(team_stats, dict):
                for k in ["pointsScored", "pointsConceded", "assistsScored", "reboundsTotal",
                          "rating", "ppg", "name", "ranking"]:
                    if k in team_stats:
                        print(f"  {k}: {team_stats[k]}")
            print(f"  (data completa guardada en bsk_raw_{name.replace(' ','_')}.json)")
            with open(f"bsk_raw_{name.replace(' ','_')}.json", "w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        print()

    # Últimos partidos
    for name, tid in [(TEAM_A, id_a), (TEAM_B, id_b)]:
        print(f"── Últimos 5 partidos: {name}")
        games = sofascore_last_games(tid, name, 5)
        if games:
            for g in games:
                print(format_game_sofascore(g, tid))
            with open(f"bsk_games_{name.replace(' ','_')}.json", "w", encoding="utf-8") as f:
                json.dump(games, f, ensure_ascii=False, indent=2)
        else:
            print("  Sin datos. Revisa los IDs de Sofascore.")
        print()

    # H2H
    print(f"── Head-to-head reciente")
    h2h = sofascore_h2h(id_a, id_b)
    if h2h:
        for g in h2h:
            print(format_game_sofascore(g, id_a))
        with open("bsk_h2h.json", "w", encoding="utf-8") as f:
            json.dump(h2h, f, ensure_ascii=False, indent=2)
    else:
        print("  Sin datos H2H.")
    print()

    print("─" * 60)
    print("Archivos .json guardados con data completa.")
    print("Pega este output + los .json en el chat para el análisis.\n")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", default="", help="API-Sports key")
    args = parser.parse_args()

    if args.key:
        run_api_sports(args.key)
    else:
        run_sofascore()
