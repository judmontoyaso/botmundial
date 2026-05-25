import os
import sys
import json
import httpx
import asyncio
from dotenv import load_dotenv

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

if not API_FOOTBALL_KEY or API_FOOTBALL_KEY == "your_api_football_key":
    print("❌ ERROR: Configura API_FOOTBALL_KEY en tu archivo .env")
    sys.exit(1)

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}
BASE_URL = "https://v3.football.api-sports.io"

async def fetch_team_info(client, team_name):
    """
    Busca el ID real y logo del equipo en API-Football.
    """
    try:
        response = await client.get(f"{BASE_URL}/teams", params={"name": team_name})
        data = response.json()
        
        if not data.get("response"):
            print(f"⚠️ Equipo no encontrado en API con el nombre: {team_name}")
            return None
            
        team_data = data["response"][0]["team"]
        return {
            "api_id": team_data["id"],
            "logo": team_data["logo"]
        }
    except Exception as e:
        print(f"❌ Error al consultar {team_name}: {e}")
        return None

async def update_stats():
    print("🌍 Conectando a API-Football para descargar IDs y logos reales...")
    
    with open("app/data/teams.json", "r", encoding="utf-8") as f:
        teams = json.load(f)

    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        # Probando la conexión
        test_resp = await client.get(f"{BASE_URL}/status")
        if test_resp.status_code != 200:
            print("❌ Error de autenticación con la API. Verifica tu API Key.")
            return

        status_data = test_resp.json()
        requests_made = status_data.get('response', {}).get('requests', {}).get('current', 0)
        requests_limit = status_data.get('response', {}).get('requests', {}).get('limit_day', 100)
        
        print(f"✅ Autenticación exitosa. Límite diario: {requests_made}/{requests_limit}")
        
        if requests_limit - requests_made < len(teams):
            print("⚠️ No hay suficientes peticiones libres para consultar a los 48 equipos hoy. Se actualizarán los posibles.")

        print("Sincronizando equipos... (esto consumirá ~48 peticiones de tu límite gratuito)")
        
        updated_count = 0
        for i, team in enumerate(teams):
            if "api_id" in team:
                continue # Ya actualizado antes
                
            info = await fetch_team_info(client, team["name"])
            if info:
                team["api_id"] = info["api_id"]
                team["logo_url"] = info["logo"]
                updated_count += 1
                print(f"  [{i+1}/48] ✔️ {team['name']} -> ID API: {info['api_id']}")
            
            # Sleep to respect rate limits (10 req / sec usually, we'll do 0.2s to be safe)
            await asyncio.sleep(0.2)

    # Save the updated teams back
    if updated_count > 0:
        with open("app/data/teams.json", "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=2, ensure_ascii=False)
        print(f"🎉 ¡Éxito! Se sincronizaron {updated_count} equipos con API-Football y se guardaron en teams.json.")
        print("👉 IMPORTANTE: Ejecuta 'python seed_supabase.py' para enviar esta nueva metadata a tu base de datos.")
    else:
        print("No se encontraron nuevos equipos para actualizar.")

if __name__ == "__main__":
    asyncio.run(update_stats())
