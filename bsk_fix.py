"""
Script de diagnóstico y análisis BSL — Türk Telekom vs Anadolu Efes
Usa los IDs encontrados: Turk Telekom=1277, Anadolu Efes=1263
"""

import requests, json

KEY = "2049efe36593167e55e65c38a1e66d9d"
BASE = "https://v1.basketball.api-sports.io"

HEADERS = {
    "x-apisports-key": KEY,
    "Accept": "application/json",
}

ID_TT   = 1277  # Turk Telekom
ID_EFES = 1263  # Anadolu Efes


def get(path, **params):
    r = requests.get(BASE + path, headers=HEADERS, params=params, timeout=15)
    return r.json()


# ── 1. Cuántas llamadas quedan ──────────────────────────────────────────────
print("── Status de la cuenta API-Sports")
r = requests.get(BASE + "/status", headers=HEADERS, timeout=10)
status = r.json()
sub = status.get("response", {}).get("subscription", {})
req = status.get("response", {}).get("requests", {})
print(f"  Plan: {sub.get('plan','?')}  Requests hoy: {req.get('current','?')}/{req.get('limit_day','?')}\n")

# ── 2. Buscar ligas de Turk Telekom ─────────────────────────────────────────
print("── Ligas donde juega Turk Telekom")
data = get("/leagues", team=ID_TT)
leagues = data.get("response", [])
for lg in leagues:
    print(f"  ID:{lg.get('id'):<6} {lg.get('name','?'):<35} País:{lg.get('country',{}).get('name','?')}")
    seasons = lg.get("seasons", [])
    if seasons:
        print(f"    Temporadas disponibles: {[s.get('season') for s in seasons[-3:]]}")
print()

# ── 3. Todos los juegos disponibles de Turk Telekom ─────────────────────────
print("── Juegos disponibles de Turk Telekom (todas las temporadas)")
for season in ["2024-2025", "2025-2026", "2025", "2026"]:
    data = get("/games", team=ID_TT, season=season)
    n = len(data.get("response", []))
    if n > 0:
        print(f"  Temporada {season}: {n} juegos encontrados")
    else:
        print(f"  Temporada {season}: sin datos")
print()

# ── 4. Últimos juegos directamente por equipo (sin filtro de liga/temporada) ─
print("── Últimos juegos de Turk Telekom (sin filtro temporada)")
data = get("/games", team=ID_TT)
games = sorted(data.get("response", []), key=lambda g: g.get("date",""), reverse=True)
if games:
    print(f"  Total encontrados: {len(games)}")
    for g in games[:10]:
        ht = g.get("teams", {}).get("home", {})
        at = g.get("teams", {}).get("away", {})
        hs = g.get("scores", {}).get("home", {}).get("total", "?")
        as_ = g.get("scores", {}).get("away", {}).get("total", "?")
        date = g.get("date","")[:10]
        status = g.get("status", {}).get("long","?")
        lg = g.get("league", {}).get("name","?")
        print(f"  {date}  {ht.get('name','?'):<25} {hs:>3} – {as_:<3} {at.get('name','?'):<25} [{lg}] {status}")
else:
    print("  Sin juegos encontrados")
print()

# ── 5. Últimos juegos de Efes ────────────────────────────────────────────────
print("── Últimos juegos de Anadolu Efes (sin filtro temporada)")
data = get("/games", team=ID_EFES)
games_efes = sorted(data.get("response", []), key=lambda g: g.get("date",""), reverse=True)
if games_efes:
    print(f"  Total encontrados: {len(games_efes)}")
    for g in games_efes[:10]:
        ht = g.get("teams", {}).get("home", {})
        at = g.get("teams", {}).get("away", {})
        hs = g.get("scores", {}).get("home", {}).get("total", "?")
        as_ = g.get("scores", {}).get("away", {}).get("total", "?")
        date = g.get("date","")[:10]
        lg = g.get("league", {}).get("name","?")
        print(f"  {date}  {ht.get('name','?'):<25} {hs:>3} – {as_:<3} {at.get('name','?'):<25} [{lg}]")
else:
    print("  Sin juegos encontrados")
print()

# ── 6. H2H directo por ID ────────────────────────────────────────────────────
print("── Head-to-head: Turk Telekom vs Anadolu Efes (por ID)")
data = get("/games", h2h=f"{ID_TT}-{ID_EFES}")
h2h = sorted(data.get("response", []), key=lambda g: g.get("date",""), reverse=True)
if h2h:
    print(f"  Total H2H encontrados: {len(h2h)}")
    for g in h2h[:8]:
        ht = g.get("teams", {}).get("home", {})
        at = g.get("teams", {}).get("away", {})
        hs = g.get("scores", {}).get("home", {}).get("total", "?")
        as_ = g.get("scores", {}).get("away", {}).get("total", "?")
        date = g.get("date","")[:10]
        lg = g.get("league", {}).get("name","?")
        print(f"  {date}  {ht.get('name','?'):<25} {hs:>3} – {as_:<3} {at.get('name','?')}  [{lg}]")
else:
    print("  Sin datos H2H")

# guardar todo para debug
with open("bsk_debug.json", "w", encoding="utf-8") as f:
    json.dump({
        "games_tt": games[:20] if games else [],
        "games_efes": games_efes[:20] if games_efes else [],
        "h2h": h2h,
    }, f, ensure_ascii=False, indent=2)
print("\nData completa guardada en bsk_debug.json")
