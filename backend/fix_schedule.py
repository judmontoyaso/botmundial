"""
Corrige el calendario del Mundial 2026 con datos oficiales (ESPN).

El schedule.json original tenía fechas, horas, sedes y emparejamientos
inventados. Este script:
  1. Descarga los 104 partidos oficiales desde la API pública de ESPN.
  2. Reescribe app/data/schedule.json con los 72 partidos de fase de grupos
     reales (fechas UTC, sedes y orden local/visitante correctos).
  3. Actualiza la tabla `matches` en Supabase emparejando por pareja de
     equipos (los grupos del sorteo ya eran correctos), corrigiendo fecha,
     sede, ciudad, orden local/visitante y match_number cronológico.
  4. Limpia la caché de ai_predictions (se regenera con el orden correcto).

Uso:  python fix_schedule.py            (solo stdlib, no requiere venv)
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "app" / "data"

ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
)
# Ventana de fase de grupos (UTC): 11 jun – 28 jun (los últimos juegos de
# grupos del 27 local caen el 28 en UTC).
DATE_RANGES = ["20260611-20260620", "20260621-20260630"]

# Abreviaturas ESPN que no coinciden con nuestro código FIFA
ESPN_NAME_TO_CODE = {
    "Bosnia-Herzegovina": "BIH",
    "Czechia": "CZE",
    "South Korea": "KOR",
    "Türkiye": "TUR",
    "Curaçao": "CUW",
    "Ivory Coast": "CIV",
    "Congo DR": "COD",
    "Cape Verde": "CPV",
    "South Africa": "RSA",
    "Saudi Arabia": "KSA",
}

ESPN_STATUS_MAP = {
    "STATUS_SCHEDULED": "scheduled",
    "STATUS_IN_PROGRESS": "live",
    "STATUS_HALFTIME": "live",
    "STATUS_FULL_TIME": "completed",
    "STATUS_FINAL": "completed",
    "STATUS_FINAL_PEN": "completed",
    "STATUS_POSTPONED": "postponed",
}


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for candidate in (HERE / ".env", HERE.parent / ".env"):
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env.setdefault(k.strip(), v.strip())
    return env


def http_json(url: str, headers: dict | None = None, method: str = "GET",
              body: dict | list | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


def fetch_official_group_fixtures(valid_codes: set[str]) -> list[dict]:
    """Descarga y normaliza los partidos de fase de grupos desde ESPN."""
    events: dict[str, dict] = {}
    for rng in DATE_RANGES:
        payload = http_json(f"{ESPN_SCOREBOARD}?dates={rng}&limit=200")
        for e in payload.get("events", []):
            events[e["id"]] = e

    def to_code(team: dict) -> str | None:
        abbr = team.get("abbreviation")
        if abbr in valid_codes:
            return abbr
        return ESPN_NAME_TO_CODE.get(team.get("displayName", ""))

    fixtures = []
    for e in sorted(events.values(), key=lambda x: (x["date"], x["id"])):
        comp = e["competitions"][0]
        home = away = None
        scores = {}
        for c in comp["competitors"]:
            code = to_code(c["team"])
            scores[c["homeAway"]] = c.get("score")
            if c["homeAway"] == "home":
                home = code
            else:
                away = code
        if not home or not away:
            continue  # llaves eliminatorias con equipos por definir
        venue = comp.get("venue") or {}
        address = venue.get("address") or {}
        city = (address.get("city") or "").split(",")[0].strip()
        status_name = (e.get("status") or {}).get("type", {}).get("name", "")
        fixtures.append({
            "home": home,
            "away": away,
            "date": e["date"].replace("Z", ":00Z") if len(e["date"]) == 17 else e["date"],
            "venue": venue.get("fullName") or "",
            "city": city,
            "status": ESPN_STATUS_MAP.get(status_name, "scheduled"),
            "home_score": scores.get("home"),
            "away_score": scores.get("away"),
        })
    return fixtures


def main() -> None:
    teams = json.loads((DATA_DIR / "teams.json").read_text(encoding="utf-8"))
    code_group = {t["code"]: t["group_letter"] for t in teams}

    print("Descargando calendario oficial desde ESPN...")
    fixtures = fetch_official_group_fixtures(set(code_group))
    if len(fixtures) != 72:
        sys.exit(f"ERROR: se esperaban 72 partidos de grupos, llegaron {len(fixtures)}")

    # Validar que cada emparejamiento sea del mismo grupo del sorteo
    for fx in fixtures:
        if code_group[fx["home"]] != code_group[fx["away"]]:
            sys.exit(f"ERROR: {fx['home']} vs {fx['away']} no comparten grupo")
    print(f"OK: 72 partidos oficiales validados contra los grupos del sorteo.")

    # ------------------------------------------------------------------
    # 1. Reescribir schedule.json
    # ------------------------------------------------------------------
    schedule = []
    for i, fx in enumerate(fixtures, start=1):
        schedule.append({
            "match_number": i,
            "stage": "group",
            "group_letter": code_group[fx["home"]],
            "home_team": fx["home"],
            "away_team": fx["away"],
            "match_date": fx["date"],
            "venue": fx["venue"],
            "city": fx["city"],
            "status": fx["status"],
        })
    out = DATA_DIR / "schedule.json"
    out.write_text(json.dumps(schedule, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"schedule.json reescrito ({out})")

    # ------------------------------------------------------------------
    # 2. Actualizar Supabase
    # ------------------------------------------------------------------
    env = load_env()
    url, key = env.get("SUPABASE_URL", ""), env.get("SUPABASE_KEY", "")
    if not url or not key:
        sys.exit("ERROR: SUPABASE_URL / SUPABASE_KEY no configurados en .env")
    base = url.rstrip("/") + "/rest/v1"
    headers = {"apikey": key, "Authorization": f"Bearer {key}",
               "Prefer": "return=minimal"}

    db_teams = http_json(f"{base}/teams?select=id,code",
                         {"apikey": key, "Authorization": f"Bearer {key}"})
    id_by_code = {t["code"]: t["id"] for t in db_teams}
    code_by_id = {t["id"]: t["code"] for t in db_teams}

    db_matches = http_json(
        f"{base}/matches?select=id,match_number,home_team_id,away_team_id",
        {"apikey": key, "Authorization": f"Bearer {key}"})
    by_pair = {}
    for m in db_matches:
        pair = frozenset({code_by_id[m["home_team_id"]], code_by_id[m["away_team_id"]]})
        by_pair[pair] = m

    # Fase A: liberar los match_number (constraint UNIQUE) antes de renumerar
    for m in db_matches:
        http_json(f"{base}/matches?id=eq.{m['id']}", headers, "PATCH",
                  {"match_number": m["match_number"] + 1000})

    swapped = 0
    missing = []
    for i, fx in enumerate(fixtures, start=1):
        pair = frozenset({fx["home"], fx["away"]})
        m = by_pair.get(pair)
        if m is None:
            missing.append(f"{fx['home']} vs {fx['away']}")
            continue
        update = {
            "match_number": i,
            "match_date": fx["date"],
            "venue": fx["venue"],
            "city": fx["city"],
            "home_team_id": id_by_code[fx["home"]],
            "away_team_id": id_by_code[fx["away"]],
        }
        if code_by_id[m["home_team_id"]] != fx["home"]:
            swapped += 1
        http_json(f"{base}/matches?id=eq.{m['id']}", headers, "PATCH", update)

    if missing:
        sys.exit(f"ERROR: partidos sin fila en la BD: {missing}")

    # Limpiar caché de predicciones AI (orden local/visitante pudo cambiar)
    http_json(f"{base}/ai_predictions?id=gte.0", headers, "DELETE")

    print(f"Supabase actualizado: 72 partidos corregidos "
          f"({swapped} con local/visitante invertido), caché AI limpiada.")
    print("Listo. El calendario ahora coincide con la programación oficial.")


if __name__ == "__main__":
    main()
