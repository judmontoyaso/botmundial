"""
Import World Cup historical data from Fjelstul World Cup Database.

Computes per-team:
  - world_cup_appearances: number of distinct tournaments participated in
  - best_finish: highest stage reached (Final > 3rd Place > Semifinal > ...)

Source: github.com/jfjelstul/worldcup (matches.csv)
Stage mapping uses stage_name column: "Group Stage", "Round of 16",
"Quarterfinal", "Semifinal", "Third-Place Match", "Final"
"""
import csv
import io
import sys
import os
import asyncio
import httpx
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == "your_supabase_url":
    print("ERROR: Configura SUPABASE_URL y SUPABASE_KEY en tu .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

MATCHES_URL = (
    "https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/matches.csv"
)

# Stage ranking: higher = better finish
STAGE_RANK: dict[str, int] = {
    "group stage": 1,
    "round of 16": 2,
    "quarterfinal": 3,
    "quarterfinals": 3,
    "semifinal": 4,
    "semifinals": 4,
    "third-place match": 5,
    "third place match": 5,
    "third place": 5,
    "final": 6,
}

STAGE_LABEL: dict[int, str] = {
    1: "Fase de Grupos",
    2: "Octavos de Final",
    3: "Cuartos de Final",
    4: "Semifinal",
    5: "Tercer Puesto",
    6: "Final",
}

# Our internal name / code → list of name variants in Fjelstul data
NAME_OVERRIDES: dict[str, list[str]] = {
    "USA": ["United States", "United States of America"],
    "KOR": ["South Korea", "Korea Republic", "Korea DPR"],
    "IRN": ["Iran", "IR Iran"],
    "CIV": ["Ivory Coast", "Côte d'Ivoire"],
    "RSA": ["South Africa"],
    "NZL": ["New Zealand"],
    "DRC": ["DR Congo", "Congo DR", "Zaire"],
    "CUW": ["Curaçao", "Curacao"],
    "TRI": ["Trinidad and Tobago", "Trinidad & Tobago"],
    "HON": ["Honduras"],
    "BOL": ["Bolivia"],
    "PAR": ["Paraguay"],
    "VEN": ["Venezuela"],
    "CZE": ["Czech Republic", "Czechoslovakia", "Czechia"],
    "TUR": ["Turkey", "Türkiye"],
    "BIH": ["Bosnia and Herzegovina", "Bosnia & Herzegovina"],
    "SCO": ["Scotland"],
    "CPV": ["Cape Verde"],
    "ALG": ["Algeria"],
    "CMR": ["Cameroon"],
    "EGY": ["Egypt"],
    "NGA": ["Nigeria"],
    "GHA": ["Ghana"],
    "TUN": ["Tunisia"],
    "SEN": ["Senegal"],
    "MAR": ["Morocco"],
    "QAT": ["Qatar"],
    "KSA": ["Saudi Arabia"],
    "UZB": ["Uzbekistan"],
    "JOR": ["Jordan"],
    "IRQ": ["Iraq"],
    "SDN": ["Sudan"],
    "HAI": ["Haiti"],
    "JAM": ["Jamaica"],
    "SLV": ["El Salvador"],
}


def _norm(s: str) -> str:
    return s.lower().strip()


async def main() -> None:
    print("Descargando datos históricos del Mundial (Fjelstul World Cup DB)...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(MATCHES_URL)

    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al descargar matches.csv")
        print("URL: " + MATCHES_URL)
        return

    reader = csv.DictReader(io.StringIO(resp.text))
    rows = list(reader)
    print(f"  {len(rows)} partidos en el CSV.")
    print(f"  Columnas disponibles: {reader.fieldnames}")

    # tournament_id or year_host identifies the tournament
    # home_team_name, away_team_name, stage_name, tournament_id (or year)
    # Detect column names (the dataset has evolved over versions)
    sample = rows[0] if rows else {}
    team_col_home = "home_team_name" if "home_team_name" in sample else "home_team"
    team_col_away = "away_team_name" if "away_team_name" in sample else "away_team"
    stage_col = "stage_name" if "stage_name" in sample else "stage"
    tournament_col = "tournament_id" if "tournament_id" in sample else "year"

    print(f"  Usando columnas: home={team_col_home}, away={team_col_away}, stage={stage_col}, tournament={tournament_col}\n")

    # Build set of (team_name_norm, tournament_id) and best stage per team
    team_tournaments: dict[str, set] = {}   # norm_name → set of tournament ids
    team_best_stage: dict[str, int] = {}    # norm_name → best STAGE_RANK

    for row in rows:
        home = _norm(row.get(team_col_home, ""))
        away = _norm(row.get(team_col_away, ""))
        stage_raw = _norm(row.get(stage_col, ""))
        tournament = row.get(tournament_col, "").strip()

        stage_rank = STAGE_RANK.get(stage_raw, 0)

        for team in (home, away):
            if not team:
                continue
            if team not in team_tournaments:
                team_tournaments[team] = set()
            team_tournaments[team].add(tournament)
            if stage_rank > team_best_stage.get(team, 0):
                team_best_stage[team] = stage_rank

    print(f"  {len(team_tournaments)} equipos únicos en el historial.")

    # Load teams from Supabase
    teams = supabase.table("teams").select("id, code, name, stats").execute().data
    print(f"  {len(teams)} equipos en Supabase.\n")

    updated = 0
    not_found: list[str] = []

    for team in teams:
        code = team["code"]
        name = team["name"]
        existing: dict = team.get("stats") or {}

        # Build candidate names
        candidates = [_norm(name)] + [_norm(n) for n in NAME_OVERRIDES.get(code, [])]

        matched_key = None
        for candidate in candidates:
            if candidate in team_tournaments:
                matched_key = candidate
                break

        if matched_key is None:
            not_found.append(f"{name} ({code})")
            continue

        appearances = len(team_tournaments[matched_key])
        best_rank = team_best_stage.get(matched_key, 0)
        best_label = STAGE_LABEL.get(best_rank, "Fase de Grupos")

        merged = {
            **existing,
            "world_cup_appearances": appearances,
            "best_finish": best_label,
        }

        supabase.table("teams").update({"stats": merged}).eq("code", code).execute()
        updated += 1
        print(f"  {name:25s} ({code})  apariciones={appearances}  mejor={best_label}")

    print(f"\nHistórico importado: {updated}/{len(teams)} equipos actualizados.")
    if not_found:
        print(f"No encontrados ({len(not_found)}): {', '.join(not_found)}")

    print("\nPRÓXIMO PASO: reinicia el backend para reflejar los cambios.")


if __name__ == "__main__":
    asyncio.run(main())
