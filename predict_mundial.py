"""
Script de prediccion del Mundial 2026.
Usa los datos y el modelo del proyecto (Poisson + ELO + xG + Forma + Clima).
Ejecutar desde la raiz del proyecto: python predict_mundial.py
"""

import json
import math
import random
import os
from collections import defaultdict

# ---------------------------------------------------------------------------
# Cargar datos
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEAMS_FILE = os.path.join(BASE_DIR, "backend", "app", "data", "teams.json")
GROUPS_FILE = os.path.join(BASE_DIR, "backend", "app", "data", "groups.json")
SCHEDULE_FILE = os.path.join(BASE_DIR, "backend", "app", "data", "schedule.json")

with open(TEAMS_FILE, encoding="utf-8") as f:
    teams_raw = json.load(f)

with open(GROUPS_FILE, encoding="utf-8") as f:
    groups = json.load(f)

with open(SCHEDULE_FILE, encoding="utf-8") as f:
    schedule = json.load(f)

# Indexar equipos por codigo
teams = {t["code"]: t for t in teams_raw}

# ---------------------------------------------------------------------------
# Constantes del modelo (de analysis.py)
# ---------------------------------------------------------------------------
MEAN_XG_FOR = 1.30
MEAN_XG_AGAINST = 1.10
MEAN_GOALS = 1.20
HOME_FACTOR = 1.04
ELO_SCALE = 3000
DC_RHO = -0.10
DRAW_BOOST = 1.35

GDP_PER_CAPITA = {
    "USA": 85000, "CAN": 55000, "MEX": 11000, "PAN": 16000, "HAI": 1700, "CUW": 20000,
    "BRA": 10000, "ARG": 13000, "COL": 7000, "URU": 17000, "ECU": 7000, "PAR": 5500,
    "FRA": 46000, "ENG": 48000, "ESP": 33000, "GER": 54000, "POR": 25000, "NED": 57000,
    "BEL": 51000, "CRO": 20000, "SUI": 92000, "AUT": 57000, "TUR": 12000, "SCO": 48000,
    "ALG": 4200, "CZE": 28000, "BIH": 8000, "NOR": 108000, "SWE": 57000,
    "JPN": 35000, "KOR": 35000, "AUS": 65000, "IRN": 6000, "KSA": 29000,
    "JOR": 5000, "QAT": 85000, "IRQ": 7000, "UZB": 3000,
    "MAR": 4000, "EGY": 4300, "SEN": 2000, "CIV": 2300, "GHA": 2200, "TUN": 3800,
    "ALG": 4200, "RSA": 7000, "COD": 600, "CPV": 4000, "NZL": 47000,
}

POPULATION_M = {
    "USA": 340, "CAN": 38, "MEX": 130, "PAN": 4, "HAI": 12, "CUW": 0.16,
    "BRA": 215, "ARG": 46, "COL": 52, "URU": 3.5, "ECU": 18, "PAR": 7,
    "FRA": 68, "ENG": 57, "ESP": 47, "GER": 83, "POR": 10, "NED": 17,
    "BEL": 11, "CRO": 4, "SUI": 8, "AUT": 9, "TUR": 85, "SCO": 5.5,
    "ALG": 46, "CZE": 10.5, "BIH": 3.3, "NOR": 5.5, "SWE": 10.5,
    "JPN": 124, "KOR": 52, "AUS": 26, "IRN": 87, "KSA": 36,
    "JOR": 10, "QAT": 3, "IRQ": 42, "UZB": 36,
    "MAR": 37, "EGY": 105, "SEN": 17, "CIV": 27, "GHA": 32, "TUN": 12,
    "ALG": 46, "RSA": 62, "COD": 100, "CPV": 0.56, "NZL": 5,
}

GDP_REF = 15_000
GDP_MAX = 0.025
POP_REF_M = 40.0
POP_MAX = 0.015

CITY_CLIMATES = {
    "Mexico City":     {"type": "altitude",  "temp": 25},
    "Guadalajara":     {"type": "altitude",  "temp": 28},
    "Monterrey":       {"type": "hot_humid", "temp": 34},
    "Miami":           {"type": "hot_humid", "temp": 31},
    "Houston":         {"type": "hot_humid", "temp": 33},
    "Arlington":       {"type": "hot",       "temp": 34},
    "Atlanta":         {"type": "hot_humid", "temp": 31},
    "Kansas City":     {"type": "warm",      "temp": 29},
    "Philadelphia":    {"type": "warm",      "temp": 27},
    "East Rutherford": {"type": "warm",      "temp": 26},
    "Foxborough":      {"type": "warm",      "temp": 25},
    "Los Angeles":     {"type": "warm",      "temp": 26},
    "Santa Clara":     {"type": "warm",      "temp": 25},
    "Seattle":         {"type": "mild",      "temp": 22},
    "Vancouver":       {"type": "mild",      "temp": 21},
    "Toronto":         {"type": "mild",      "temp": 24},
}

# ---------------------------------------------------------------------------
# Funciones del modelo
# ---------------------------------------------------------------------------

def gdp_modifier(code):
    gdp = GDP_PER_CAPITA.get(code.upper(), GDP_REF)
    raw = math.log(gdp / GDP_REF)
    scale = GDP_MAX / math.log(108_000 / GDP_REF)
    return max(-GDP_MAX, min(GDP_MAX, raw * scale))


def pop_modifier(code):
    pop = POPULATION_M.get(code.upper(), POP_REF_M)
    raw = math.log(max(pop, 0.1) / POP_REF_M)
    scale = POP_MAX / math.log(340 / POP_REF_M)
    return max(-POP_MAX, min(POP_MAX, raw * scale))


def climate_modifier(confed, city):
    if city not in CITY_CLIMATES:
        return 0.0
    ctype = CITY_CLIMATES[city]["type"]
    confed = confed.upper()
    if ctype == "altitude":
        if confed in ("CONMEBOL", "CONCACAF"): return 0.08
        if confed == "UEFA": return -0.10
        return -0.05
    if ctype in ("hot_humid", "hot"):
        if confed in ("CAF", "CONMEBOL", "CONCACAF"): return 0.06
        if confed == "UEFA": return -0.08
        return 0.0
    if ctype == "mild":
        if confed == "UEFA": return 0.05
        return 0.0
    return 0.0


def continent_advantage(confed):
    confed = confed.upper()
    if confed == "CONCACAF": return 0.12
    if confed == "CONMEBOL": return 0.07
    return 0.0


def form_modifier(team):
    return round((team["stats"]["form_last_5"] - 2.5) / 25.0, 4)


def poisson_pmf(k, lam):
    if lam <= 0 or k < 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_sample(lam):
    if lam <= 0:
        return 0
    lam = min(lam, 30.0)
    L = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= L:
            return k - 1


def compute_lambdas(home, away, city=""):
    hs = home["stats"]
    aws = away["stats"]
    ha = hs["xg_for_avg"] / MEAN_XG_FOR
    hd = hs["xg_against_avg"] / MEAN_XG_AGAINST
    aa = aws["xg_for_avg"] / MEAN_XG_FOR
    ad = aws["xg_against_avg"] / MEAN_XG_AGAINST

    lh = ha * ad * MEAN_GOALS * HOME_FACTOR
    la = aa * hd * MEAN_GOALS

    # Clima + continente
    lh *= (1.0 + climate_modifier(home["confederation"], city) + continent_advantage(home["confederation"]))
    la *= (1.0 + climate_modifier(away["confederation"], city) + continent_advantage(away["confederation"]))

    # ELO
    elo_diff = hs["elo_rating"] - aws["elo_rating"]
    factor = elo_diff / ELO_SCALE
    lh = max(0.3, lh * (1.0 + factor))
    la = max(0.3, la * (1.0 - factor))

    # Forma reciente
    lh = max(0.3, lh * (1.0 + form_modifier(home)))
    la = max(0.3, la * (1.0 + form_modifier(away)))

    # GDP + Poblacion (peso 40%)
    lh = max(0.3, lh * (1.0 + gdp_modifier(home["code"]) * 0.4 + pop_modifier(home["code"]) * 0.4))
    la = max(0.3, la * (1.0 + gdp_modifier(away["code"]) * 0.4 + pop_modifier(away["code"]) * 0.4))

    return round(lh, 4), round(la, 4)


def build_matrix(lh, la, max_g=5):
    n = max_g + 1
    matrix = [[poisson_pmf(h, lh) * poisson_pmf(a, la) for a in range(n)] for h in range(n)]
    # Dixon-Coles
    rho = DC_RHO
    matrix[0][0] *= max(0.0, 1 - lh * la * rho)
    matrix[1][0] *= max(0.0, 1 + la * rho)
    matrix[0][1] *= max(0.0, 1 + lh * rho)
    matrix[1][1] *= max(0.0, 1 - rho)
    for g in range(n):
        matrix[g][g] *= DRAW_BOOST
    total = sum(matrix[h][a] for h in range(n) for a in range(n))
    if total > 0:
        matrix = [[matrix[h][a] / total for a in range(n)] for h in range(n)]
    return matrix


def derive_probs(matrix):
    n = len(matrix)
    hw = sum(matrix[h][a] for h in range(n) for a in range(n) if h > a)
    dr = sum(matrix[h][h] for h in range(n))
    aw = sum(matrix[h][a] for h in range(n) for a in range(n) if a > h)
    total = hw + dr + aw
    if total > 0:
        hw /= total; dr /= total; aw /= total
    return round(hw, 4), round(dr, 4), round(aw, 4)


# ---------------------------------------------------------------------------
# Simulacion de partido knockout
# ---------------------------------------------------------------------------

_lam_cache = {}

def get_lams(hc, ac, city=""):
    key = (hc, ac)
    if key not in _lam_cache:
        home = teams.get(hc)
        away = teams.get(ac)
        if home and away:
            _lam_cache[key] = compute_lambdas(home, away, city)
        else:
            _lam_cache[key] = (1.2, 1.0)
    return _lam_cache[key]


def sim_knockout(hc, ac, city=""):
    lh, la = get_lams(hc, ac, city)
    h, a = poisson_sample(lh), poisson_sample(la)
    if h != a:
        return hc if h > a else ac
    # Penales: coin flip sesgado por ELO
    elo_h = teams[hc]["stats"]["elo_rating"] if hc in teams else 1700
    elo_a = teams[ac]["stats"]["elo_rating"] if ac in teams else 1700
    p = 0.5 + (elo_h - elo_a) / 6000.0
    return hc if random.random() < p else ac


# ---------------------------------------------------------------------------
# Simulacion de fase de grupos
# ---------------------------------------------------------------------------

group_matches = [m for m in schedule if m["stage"] == "group"]

# Precomputar lambdas para todos los partidos de grupos
for m in group_matches:
    hc = m.get("home_team") or m.get("home_team_code")
    ac = m.get("away_team") or m.get("away_team_code")
    city = m.get("city", "")
    if hc and ac:
        get_lams(hc, ac, city)

# Estructura de grupos
group_structure = {}
group_match_list = []
for m in group_matches:
    g = m["group_letter"]
    hc = m.get("home_team") or m.get("home_team_code")
    ac = m.get("away_team") or m.get("away_team_code")
    city = m.get("city", "")
    if g not in group_structure:
        group_structure[g] = []
    if hc and hc not in group_structure[g]:
        group_structure[g].append(hc)
    if ac and ac not in group_structure[g]:
        group_structure[g].append(ac)
    group_match_list.append((g, hc, ac, city))

sorted_groups = sorted(group_structure.keys())

# ---------------------------------------------------------------------------
# Monte Carlo: 10,000 simulaciones
# ---------------------------------------------------------------------------

N_SIM = 10_000
random.seed(42)

champion_c = defaultdict(int)
finalist_c = defaultdict(int)
top4_c = defaultdict(int)
top8_c = defaultdict(int)
advance_c = defaultdict(int)

# Tambien rastrear goles por equipo para aproximar goleador por seleccion
goals_by_team = defaultdict(list)  # code -> lista de goles totales por sim

print(f"Ejecutando {N_SIM:,} simulaciones Monte Carlo del Mundial 2026...")

for sim_i in range(N_SIM):
    pts = defaultdict(int)
    gf = defaultdict(int)
    ga = defaultdict(int)
    sim_goals_by_team = defaultdict(int)

    for g, hc, ac, city in group_match_list:
        lh, la = get_lams(hc, ac, city)
        h, a = poisson_sample(lh), poisson_sample(la)
        gf[hc] += h; ga[hc] += a
        gf[ac] += a; ga[ac] += h
        sim_goals_by_team[hc] += h
        sim_goals_by_team[ac] += a
        if h > a:   pts[hc] += 3
        elif a > h: pts[ac] += 3
        else:       pts[hc] += 1; pts[ac] += 1

    qualifiers = []
    thirds = []

    for g in sorted_groups:
        ranked = sorted(
            group_structure[g],
            key=lambda c: (pts[c], gf[c] - ga[c], gf[c]),
            reverse=True,
        )
        qualifiers.append(ranked[0])
        qualifiers.append(ranked[1])
        advance_c[ranked[0]] += 1
        advance_c[ranked[1]] += 1
        if len(ranked) >= 3:
            t = ranked[2]
            thirds.append((pts[t], gf[t] - ga[t], gf[t], t))

    thirds.sort(reverse=True)
    for _, _, _, t in thirds[:8]:
        qualifiers.append(t)
        advance_c[t] += 1

    # Knockout: R32 → R16 → QF → SF → Final
    if len(qualifiers) >= 32:
        r32_w = [sim_knockout(qualifiers[i], qualifiers[i+1]) for i in range(0, 32, 2)]
    else:
        r32_w = qualifiers

    r16_w = [sim_knockout(r32_w[i], r32_w[i+1]) for i in range(0, len(r32_w), 2)]
    qf_w  = [sim_knockout(r16_w[i], r16_w[i+1]) for i in range(0, len(r16_w), 2)]
    sf_w  = [sim_knockout(qf_w[i],  qf_w[i+1])  for i in range(0, len(qf_w), 2)]
    winner = sf_w[0] if len(sf_w) == 1 else sim_knockout(sf_w[0], sf_w[1])

    # Goles en fase eliminatoria (aproximacion via lambda esperada)
    rounds_played = defaultdict(int)
    all_ko = r32_w + r16_w + qf_w + sf_w + [winner]
    for code in all_ko:
        rounds_played[code] += 1
    for code, rds in rounds_played.items():
        for _ in range(rds):
            lh, _ = get_lams(code, winner if code != winner else r32_w[0])
            sim_goals_by_team[code] += poisson_sample(lh)

    for c in r16_w: top8_c[c] += 1
    for c in qf_w:  top4_c[c] += 1
    for c in sf_w:  finalist_c[c] += 1
    champion_c[winner] += 1

    for code, g in sim_goals_by_team.items():
        goals_by_team[code].append(g)

# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------

results = []
for code, t in teams.items():
    results.append({
        "code": code,
        "name": t["name"],
        "flag": t["flag_emoji"],
        "elo": t["stats"]["elo_rating"],
        "confederation": t["confederation"],
        "xg_for": t["stats"]["xg_for_avg"],
        "xg_against": t["stats"]["xg_against_avg"],
        "form_5": t["stats"]["form_last_5"],
        "fifa_ranking": t["fifa_ranking"],
        "p_champion":      round(champion_c.get(code, 0) / N_SIM * 100, 2),
        "p_finalist":      round(finalist_c.get(code, 0) / N_SIM * 100, 2),
        "p_top4":          round(top4_c.get(code, 0)     / N_SIM * 100, 2),
        "p_top8":          round(top8_c.get(code, 0)     / N_SIM * 100, 2),
        "p_group_advance": round(advance_c.get(code, 0)  / N_SIM * 100, 2),
        "avg_goals": round(sum(goals_by_team[code]) / max(len(goals_by_team[code]), 1), 2),
    })

results.sort(key=lambda x: x["p_champion"], reverse=True)

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

SEPARATOR = "=" * 80

print(f"\n{SEPARATOR}")
print(f"  PREDICCIONES MUNDIAL 2026 — Modelo Poisson+ELO+xG+Forma ({N_SIM:,} simulaciones)")
print(f"{SEPARATOR}")

print(f"\n{'CANDIDATOS AL CAMPEON':^80}")
print(f"{'-'*80}")
print(f"{'#':<3} {'Equipo':<22} {'ELO':>5} {'xG+':>5} {'xG-':>5} {'Campeon':>8} {'Final':>7} {'Top4':>7} {'Top8':>7} {'Grupos':>7}")
print(f"{'-'*80}")
for i, r in enumerate(results[:16], 1):
    print(f"{i:<3} {r['flag']} {r['name']:<20} {r['elo']:>5} {r['xg_for']:>5.2f} {r['xg_against']:>5.2f} {r['p_champion']:>7.1f}% {r['p_finalist']:>6.1f}% {r['p_top4']:>6.1f}% {r['p_top8']:>6.1f}% {r['p_group_advance']:>6.1f}%")

# Top goleadores por promedio de goles esperados
print(f"\n{SEPARATOR}")
print(f"  EQUIPOS CON MAYOR PRODUCCION GOLEADORA (basado en xG + fases alcanzadas)")
print(f"{SEPARATOR}")
results_by_goals = sorted(results, key=lambda x: x["avg_goals"], reverse=True)
print(f"\n{'#':<3} {'Equipo':<22} {'xG/partido':>10} {'Goles sim.':>12} {'Fase esperada'}")
print(f"{'-'*70}")
for i, r in enumerate(results_by_goals[:12], 1):
    if r["p_top4"] >= 20:
        fase = "Semifinal+"
    elif r["p_top8"] >= 30:
        fase = "Cuartos+"
    elif r["p_group_advance"] >= 70:
        fase = "Octavos+"
    else:
        fase = "Grupos"
    print(f"{i:<3} {r['flag']} {r['name']:<20} {r['xg_for']:>10.2f} {r['avg_goals']:>12.2f}    {fase}")

# Colombia especificamente
print(f"\n{SEPARATOR}")
print(f"  COLOMBIA — ANALISIS DETALLADO")
print(f"{SEPARATOR}")
col = next((r for r in results if r["code"] == "COL"), None)
if col:
    print(f"\n  {col['flag']} Colombia")
    print(f"  Grupo K: Portugal (ELO 2000), Uzbekistan (ELO 1570), DR Congo (ELO 1585)")
    print(f"\n  ELO Rating:        {col['elo']}")
    print(f"  FIFA Ranking:      #{col['fifa_ranking']}")
    print(f"  xG ofensivo/pj:    {col['xg_for']}")
    print(f"  xG defensivo/pj:   {col['xg_against']}")
    print(f"  Forma ultimos 5:   {col['form_5']}/5 victorias")
    print(f"\n  PROBABILIDADES:")
    print(f"    Avanzar de Grupos: {col['p_group_advance']:>6.1f}%")
    print(f"    Llegar a Top 8:    {col['p_top8']:>6.1f}%")
    print(f"    Llegar a Top 4:    {col['p_top4']:>6.1f}%")
    print(f"    Llegar a Final:    {col['p_finalist']:>6.1f}%")
    print(f"    Ser CAMPEON:       {col['p_champion']:>6.1f}%")

    # Estimar fase mas probable
    if col["p_champion"] >= 5:
        fase_col = "FINAL (candidato al titulo)"
    elif col["p_finalist"] >= 10:
        fase_col = "SEMIFINALES"
    elif col["p_top4"] >= 20:
        fase_col = "CUARTOS DE FINAL"
    elif col["p_top8"] >= 40:
        fase_col = "OCTAVOS DE FINAL"
    elif col["p_group_advance"] >= 60:
        fase_col = "OCTAVOS DE FINAL"
    else:
        fase_col = "FASE DE GRUPOS"

    print(f"\n  >>> FASE ESPERADA PARA COLOMBIA: {fase_col}")

# Resumen final
print(f"\n{SEPARATOR}")
print(f"  RESUMEN DE PREDICCIONES")
print(f"{SEPARATOR}")
champion = results[0]
print(f"\n  CAMPEON PREDICHO:   {champion['flag']} {champion['name']} ({champion['p_champion']:.1f}% de probabilidad)")
print(f"  ELO: {champion['elo']} | xG: {champion['xg_for']}/{champion['xg_against']}")
print(f"  FIFA #{champion['fifa_ranking']} | Confederacion: {champion['confederation']}")

finalist = results[1]
print(f"\n  SUBCAMPEON PREDICHO: {finalist['flag']} {finalist['name']} ({finalist['p_finalist']:.1f}% chance de final)")

# Goleador: jugador con mayor xG de equipo con mayor produccion
print(f"\n  GOLEADOR PREDICHO DEL TORNEO:")
top_scorer_candidates = [
    ("Kylian Mbappe",     "FRA", "🇫🇷", 2048, 1.95),
    ("Erling Haaland",    "NOR", "🇳🇴", 1785, 1.30),  # NOR tiene a Haaland
    ("Lionel Messi",      "ARG", "🇦🇷", 2062, 1.85),
    ("Vinicius Jr.",      "BRA", "🇧🇷", 2045, 1.80),
    ("Harry Kane",        "ENG", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 2030, 1.75),
    ("Robert Lewandowski","POL", "🇵🇱", 1800, 1.55),  # POL no clasifico, usar sustituto
    ("Lamine Yamal",      "ESP", "🇪🇸", 2000, 1.90),
    ("Cristiano Ronaldo", "POR", "🇵🇹", 2000, 1.80),
    ("Luis Diaz",         "COL", "🇨🇴", 1865, 1.50),
    ("Bukayo Saka",       "ENG", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 2030, 1.75),
]

# Puntuar candidatos: xG individual * prob_fases del equipo
def score_scorer(player, team_code, xg_team, elo):
    team_r = next((r for r in results if r["code"] == team_code), None)
    if not team_r:
        return 0
    # Score: xG equipo * (prob avanzar de grupos + prob top8*2 + prob top4*3 + prob campeon*5)
    phase_weight = (
        team_r["p_group_advance"] / 100 * 1 +
        team_r["p_top8"] / 100 * 2 +
        team_r["p_top4"] / 100 * 3 +
        team_r["p_finalist"] / 100 * 4 +
        team_r["p_champion"] / 100 * 5
    )
    return xg_team * phase_weight

scored = [(name, flag, team, xg, score_scorer(name, team, xg, elo)) for name, team, flag, elo, xg in top_scorer_candidates]
scored.sort(key=lambda x: x[4], reverse=True)

print(f"\n  {'Jugador':<25} {'Equipo':<12} {'xG equipo':>10}  {'Score modelo':>12}")
print(f"  {'-'*65}")
for name, flag, team, xg, sc in scored[:8]:
    team_r = next((r for r in results if r["code"] == team), None)
    team_name = team_r["name"] if team_r else team
    print(f"  {name:<25} {flag} {team_name:<10} {xg:>10.2f}  {sc:>12.3f}")

top_scorer = scored[0]
print(f"\n  >>> GOLEADOR PREDICHO: {top_scorer[0]} ({top_scorer[1]} {next((r['name'] for r in results if r['code']==top_scorer[2]), top_scorer[2])})")

if col:
    print(f"\n  >>> COLOMBIA: {col['flag']} Fase esperada: {fase_col}")

print(f"\n{SEPARATOR}\n")
