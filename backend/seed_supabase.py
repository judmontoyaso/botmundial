import json
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == "your_supabase_url":
    print("❌ ERROR: Configura SUPABASE_URL y SUPABASE_KEY en tu archivo .env")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def seed_database():
    print("🌱 Iniciando la migración de datos a Supabase...")

    # Limpiar predicciones AI cacheadas (se regeneran con el nuevo modelo Poisson)
    try:
        supabase.table("ai_predictions").delete().neq("id", 0).execute()
        print("🧹 Caché de predicciones AI eliminada (se regenerará con modelo Poisson).")
    except Exception as e:
        print(f"⚠️  No se pudo limpiar ai_predictions: {e}")

    # 1. Insert Teams
    try:
        with open("app/data/teams.json", "r", encoding="utf-8") as f:
            teams_data = json.load(f)
        
        print(f"Encontrados {len(teams_data)} equipos en JSON. Insertando...")
        for team in teams_data:
            data = {
                "name": team["name"],
                "code": team["code"],
                "group_letter": team["group_letter"],
                "fifa_ranking": team.get("fifa_ranking"),
                "confederation": team.get("confederation"),
                "flag_emoji": team.get("flag_emoji"),
                "stats": team.get("stats", {})
            }
            # Upsert para no duplicar si ya existe el código
            supabase.table("teams").upsert(data, on_conflict="code").execute()
        
        print("✅ Equipos insertados/actualizados correctamente.")
    except Exception as e:
        print(f"❌ Error al insertar equipos: {e}")

    # 2. Get the team IDs from Supabase to map them to matches
    try:
        response = supabase.table("teams").select("id, code").execute()
        team_map = {t["code"]: t["id"] for t in response.data}
    except Exception as e:
        print(f"❌ Error al obtener los IDs de los equipos: {e}")
        return

    # 3. Insert Matches
    try:
        with open("app/data/schedule.json", "r", encoding="utf-8") as f:
            matches_data = json.load(f)
            
        print(f"Encontrados {len(matches_data)} partidos en JSON. Insertando...")
        for match in matches_data:
            home_code = match["home_team"]
            away_code = match["away_team"]
            
            home_id = team_map.get(home_code)
            away_id = team_map.get(away_code)
            
            if not home_id or not away_id:
                print(f"  ⚠️ Saltando partido {home_code} vs {away_code}: Equipo no encontrado en DB")
                continue
                
            data = {
                "match_number": match["match_number"],
                "stage": match["stage"],
                "group_letter": match.get("group_letter"),
                "home_team_id": home_id,
                "away_team_id": away_id,
                "match_date": match["match_date"],
                "venue": match.get("venue"),
                "city": match.get("city"),
                "status": match.get("status", "scheduled")
            }
            
            # Upsert by match_number
            supabase.table("matches").upsert(data, on_conflict="match_number").execute()
            
        print("✅ Partidos insertados/actualizados correctamente.")
    except Exception as e:
        print(f"❌ Error al insertar partidos: {e}")

    print("🎉 Migración completada. Tu base de datos ya tiene todos los datos.")

if __name__ == "__main__":
    seed_database()
