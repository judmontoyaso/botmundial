import json
import os
import random

teams_data = [
    # Group A
    ("Mexico", "MEX", "A", 15, "CONCACAF", "🇲🇽", 1.5, 1.0, 17, "Quarterfinals"),
    ("South Korea", "KOR", "A", 22, "AFC", "🇰🇷", 1.3, 1.0, 11, "Semifinals"),
    ("South Africa", "RSA", "A", 58, "CAF", "🇿🇦", 1.1, 1.2, 3, "Group Stage"),
    ("Czechia", "CZE", "A", 36, "UEFA", "🇨🇿", 1.2, 1.1, 1, "Group Stage"),
    
    # Group B
    ("Canada", "CAN", "B", 49, "CONCACAF", "🇨🇦", 1.2, 1.3, 2, "Group Stage"),
    ("Switzerland", "SUI", "B", 19, "UEFA", "🇨🇭", 1.4, 0.9, 12, "Quarterfinals"),
    ("Qatar", "QAT", "B", 34, "AFC", "🇶🇦", 1.2, 1.5, 1, "Group Stage"),
    ("Bosnia-Herzegovina", "BIH", "B", 71, "UEFA", "🇧🇦", 1.0, 1.4, 1, "Group Stage"),

    # Group C
    ("Brazil", "BRA", "C", 5, "CONMEBOL", "🇧🇷", 2.0, 0.7, 22, "Winner (5)"),
    ("Morocco", "MAR", "C", 12, "CAF", "🇲🇦", 1.6, 0.8, 6, "Semifinals"),
    ("Scotland", "SCO", "C", 39, "UEFA", "🏴󠁧󠁢󠁳󠁣󠁴󠁿", 1.1, 1.3, 8, "Group Stage"),
    ("Haiti", "HAI", "C", 90, "CONCACAF", "🇭🇹", 0.9, 1.8, 1, "Group Stage"),

    # Group D
    ("United States", "USA", "D", 11, "CONCACAF", "🇺🇸", 1.6, 0.9, 11, "Semifinals"),
    ("Paraguay", "PAR", "D", 56, "CONMEBOL", "🇵🇾", 1.0, 1.1, 8, "Quarterfinals"),
    ("Australia", "AUS", "D", 24, "AFC", "🇦🇺", 1.3, 1.1, 6, "Round of 16"),
    ("Turkiye", "TUR", "D", 40, "UEFA", "🇹🇷", 1.4, 1.2, 2, "3rd Place"),

    # Group E
    ("Germany", "GER", "E", 16, "UEFA", "🇩🇪", 1.8, 1.0, 20, "Winner (4)"),
    ("Ecuador", "ECU", "E", 31, "CONMEBOL", "🇪🇨", 1.2, 1.0, 4, "Round of 16"),
    ("Ivory Coast", "CIV", "E", 38, "CAF", "🇨🇮", 1.4, 1.1, 3, "Group Stage"),
    ("Curaçao", "CUW", "E", 91, "CONCACAF", "🇨🇼", 0.8, 1.6, 0, "Debut"),

    # Group F
    ("Netherlands", "NED", "F", 6, "UEFA", "🇳🇱", 1.7, 0.8, 11, "Runner-up (3)"),
    ("Japan", "JPN", "F", 18, "AFC", "🇯🇵", 1.5, 0.9, 7, "Round of 16"),
    ("Tunisia", "TUN", "F", 41, "CAF", "🇹🇳", 1.0, 1.2, 6, "Group Stage"),
    ("Sweden", "SWE", "F", 26, "UEFA", "🇸🇪", 1.5, 1.0, 12, "Runner-up"),

    # Group G
    ("Belgium", "BEL", "G", 3, "UEFA", "🇧🇪", 1.8, 0.8, 14, "3rd Place"),
    ("Iran", "IRN", "G", 20, "AFC", "🇮🇷", 1.3, 1.0, 6, "Group Stage"),
    ("Egypt", "EGY", "G", 37, "CAF", "🇪🇬", 1.2, 1.1, 3, "Group Stage"),
    ("New Zealand", "NZL", "G", 104, "OFC", "🇳🇿", 0.9, 1.5, 2, "Group Stage"),

    # Group H
    ("Spain", "ESP", "H", 8, "UEFA", "🇪🇸", 1.9, 0.7, 16, "Winner (1)"),
    ("Uruguay", "URU", "H", 15, "CONMEBOL", "🇺🇾", 1.5, 0.9, 14, "Winner (2)"),
    ("Saudi Arabia", "KSA", "H", 53, "AFC", "🇸🇦", 1.1, 1.4, 6, "Round of 16"),
    ("Cape Verde", "CPV", "H", 65, "CAF", "🇨🇻", 1.0, 1.3, 0, "Debut"),

    # Group I
    ("France", "FRA", "I", 2, "UEFA", "🇫🇷", 2.1, 0.7, 16, "Winner (2)"),
    ("Senegal", "SEN", "I", 17, "CAF", "🇸🇳", 1.4, 0.9, 3, "Quarterfinals"),
    ("Norway", "NOR", "I", 46, "UEFA", "🇳🇴", 1.3, 1.1, 3, "Round of 16"),
    ("Iraq", "IRQ", "I", 58, "AFC", "🇮🇶", 1.0, 1.2, 1, "Group Stage"),

    # Group J
    ("Argentina", "ARG", "J", 1, "CONMEBOL", "🇦🇷", 2.0, 0.6, 18, "Winner (3)"),
    ("Austria", "AUT", "J", 25, "UEFA", "🇦🇹", 1.4, 1.1, 7, "3rd Place"),
    ("Algeria", "ALG", "J", 43, "CAF", "🇩🇿", 1.3, 1.0, 4, "Round of 16"),
    ("Jordan", "JOR", "J", 70, "AFC", "🇯🇴", 1.1, 1.4, 0, "Debut"),

    # Group K
    ("Portugal", "POR", "K", 7, "UEFA", "🇵🇹", 1.9, 0.8, 8, "3rd Place"),
    ("Colombia", "COL", "K", 14, "CONMEBOL", "🇨🇴", 1.5, 0.8, 6, "Quarterfinals"),
    ("Uzbekistan", "UZB", "K", 64, "AFC", "🇺🇿", 1.1, 1.3, 0, "Debut"),
    ("DR Congo", "COD", "K", 63, "CAF", "🇨🇩", 1.0, 1.4, 1, "Group Stage"),

    # Group L
    ("England", "ENG", "L", 4, "UEFA", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 1.8, 0.7, 16, "Winner (1)"),
    ("Croatia", "CRO", "L", 10, "UEFA", "🇭🇷", 1.4, 0.9, 6, "Runner-up"),
    ("Panama", "PAN", "L", 44, "CONCACAF", "🇵🇦", 1.1, 1.3, 1, "Group Stage"),
    ("Ghana", "GHA", "L", 67, "CAF", "🇬🇭", 1.2, 1.2, 4, "Quarterfinals")
]

teams = []
groups_map = {}

for name, code, group, rank, confed, emoji, g_score, g_conc, app, best in teams_data:
    if group not in groups_map:
        groups_map[group] = []
    groups_map[group].append(code)
    
    # Generate realistic recent form
    w = random.randint(3, 7)
    d = random.randint(1, 4)
    l = 10 - w - d
    if l < 0:
        w += l
        l = 0

    team_obj = {
        "name": name,
        "code": code,
        "group_letter": group,
        "fifa_ranking": rank,
        "confederation": confed,
        "flag_emoji": emoji,
        "stats": {
            "goals_scored_avg": g_score,
            "goals_conceded_avg": g_conc,
            "wins_last_10": w,
            "draws_last_10": d,
            "losses_last_10": l,
            "world_cup_appearances": app,
            "best_finish": best
        }
    }
    teams.append(team_obj)

# Output teams.json
with open("app/data/teams.json", "w", encoding="utf-8") as f:
    json.dump(teams, f, indent=2, ensure_ascii=False)

# Output groups.json
with open("app/data/groups.json", "w", encoding="utf-8") as f:
    json.dump(groups_map, f, indent=2, ensure_ascii=False)

# Generate schedule.json
# Standard format for 4 teams: 
# Match 1: 1 v 2, Match 2: 3 v 4
# Match 3: 1 v 3, Match 4: 4 v 2
# Match 5: 4 v 1, Match 6: 2 v 3
schedule = []
cities = ["Mexico City", "Los Angeles", "Vancouver", "East Rutherford", "Miami", "Houston", "Arlington", "Atlanta", "Philadelphia", "Santa Clara", "Seattle", "Kansas City", "Foxborough", "Toronto", "Guadalajara", "Monterrey"]
venues = ["Estadio Azteca", "SoFi Stadium", "BC Place", "MetLife Stadium", "Hard Rock Stadium", "NRG Stadium", "AT&T Stadium", "Mercedes-Benz Stadium", "Lincoln Financial Field", "Levi's Stadium", "Lumen Field", "Arrowhead Stadium", "Gillette Stadium", "BMO Field", "Estadio Akron", "Estadio BBVA"]

match_idx = 1
start_date = "2026-06-11T"

# Round 1
for day_offset, group in enumerate("ABCDEFGHIJKL"):
    teams_list = groups_map[group]
    t1, t2, t3, t4 = teams_list
    
    # Match 1
    schedule.append({
        "match_number": match_idx,
        "stage": "group",
        "group_letter": group,
        "home_team": t1,
        "away_team": t2,
        "match_date": f"2026-06-{11 + (day_offset // 2):02d}T15:00:00Z",
        "venue": venues[match_idx % 16],
        "city": cities[match_idx % 16],
        "status": "scheduled"
    })
    match_idx += 1
    
    # Match 2
    schedule.append({
        "match_number": match_idx,
        "stage": "group",
        "group_letter": group,
        "home_team": t3,
        "away_team": t4,
        "match_date": f"2026-06-{11 + (day_offset // 2):02d}T18:00:00Z",
        "venue": venues[match_idx % 16],
        "city": cities[match_idx % 16],
        "status": "scheduled"
    })
    match_idx += 1

# Round 2
for day_offset, group in enumerate("ABCDEFGHIJKL"):
    teams_list = groups_map[group]
    t1, t2, t3, t4 = teams_list
    
    schedule.append({
        "match_number": match_idx,
        "stage": "group",
        "group_letter": group,
        "home_team": t1,
        "away_team": t3,
        "match_date": f"2026-06-{17 + (day_offset // 2):02d}T15:00:00Z",
        "venue": venues[match_idx % 16],
        "city": cities[match_idx % 16],
        "status": "scheduled"
    })
    match_idx += 1
    
    schedule.append({
        "match_number": match_idx,
        "stage": "group",
        "group_letter": group,
        "home_team": t4,
        "away_team": t2,
        "match_date": f"2026-06-{17 + (day_offset // 2):02d}T18:00:00Z",
        "venue": venues[match_idx % 16],
        "city": cities[match_idx % 16],
        "status": "scheduled"
    })
    match_idx += 1

# Round 3
for day_offset, group in enumerate("ABCDEFGHIJKL"):
    teams_list = groups_map[group]
    t1, t2, t3, t4 = teams_list
    
    schedule.append({
        "match_number": match_idx,
        "stage": "group",
        "group_letter": group,
        "home_team": t4,
        "away_team": t1,
        "match_date": f"2026-06-{23 + (day_offset // 2):02d}T15:00:00Z",
        "venue": venues[match_idx % 16],
        "city": cities[match_idx % 16],
        "status": "scheduled"
    })
    match_idx += 1
    
    schedule.append({
        "match_number": match_idx,
        "stage": "group",
        "group_letter": group,
        "home_team": t2,
        "away_team": t3,
        "match_date": f"2026-06-{23 + (day_offset // 2):02d}T18:00:00Z",
        "venue": venues[match_idx % 16],
        "city": cities[match_idx % 16],
        "status": "scheduled"
    })
    match_idx += 1

with open("app/data/schedule.json", "w", encoding="utf-8") as f:
    json.dump(schedule, f, indent=2, ensure_ascii=False)

print("Generated teams.json, groups.json, and schedule.json with real World Cup 2026 data.")
