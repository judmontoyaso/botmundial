"""
Import FiveThirtyEight SPI international team ratings into Supabase.

Updates xg_for_avg and xg_against_avg using calibrated off/def ratings.
Also stores spi_rating as a cross-reference field.

Source: github.com/fivethirtyeight/data/master/soccer-spi
  - off  = expected goals scored per match (≈ xg_for_avg)
  - def  = expected goals conceded per match (≈ xg_against_avg)
  - spi  = overall team quality index (0-100)
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

SPI_URL = (
    "https://projects.fivethirtyeight.com/soccer-api/international/spi_global_rankings_intl.csv"
)

# Our code → list of name variants to try in SPI data
NAME_OVERRIDES: dict[str, list[str]] = {
    "KOR": ["South Korea"],
    "USA": ["United States"],
    "IRN": ["Iran"],
    "CIV": ["Ivory Coast"],
    "RSA": ["South Africa"],
    "NZL": ["New Zealand"],
    "DRC": ["DR Congo", "Congo DR", "Congo"],
    "HAI": ["Haiti"],
    "JAM": ["Jamaica"],
    "CUW": ["Curacao", "Curaçao"],
    "TRI": ["Trinidad & Tobago", "Trinidad and Tobago"],
    "HON": ["Honduras"],
    "BOL": ["Bolivia"],
    "PAR": ["Paraguay"],
    "VEN": ["Venezuela"],
    "QAT": ["Qatar"],
    "KSA": ["Saudi Arabia"],
    "ALG": ["Algeria"],
    "COD": ["Congo", "DR Congo"],
    "CZE": ["Czech Republic", "Czechia"],
    "TUR": ["Turkey", "Türkiye"],
    "BIH": ["Bosnia & Herzegovina", "Bosnia and Herzegovina"],
    "SCO": ["Scotland"],
    "CPV": ["Cape Verde"],
    "UZB": ["Uzbekistan"],
    "JOR": ["Jordan"],
    "IRQ": ["Iraq"],
    "CMR": ["Cameroon"],
    "EGY": ["Egypt"],
    "NGA": ["Nigeria"],
    "GHA": ["Ghana"],
    "TUN": ["Tunisia"],
    "SEN": ["Senegal"],
    "MAR": ["Morocco"],
    "SDN": ["Sudan"],
}


def _norm(s: str) -> str:
    return s.lower().strip()


async def main() -> None:
    print("Descargando SPI internacional de FiveThirtyEight...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(SPI_URL)

    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al descargar SPI.")
        print("Verifica que la URL sigue activa: " + SPI_URL)
        return

    reader = csv.DictReader(io.StringIO(resp.text))
    rows = list(reader)
    print(f"  {len(rows)} equipos en el CSV.")
    print(f"  Columnas: {reader.fieldnames}")

    # Build lookup: normalized name → row
    spi_lookup: dict[str, dict] = {}
    for row in rows:
        spi_lookup[_norm(row["name"])] = row

    # Load teams from Supabase
    teams = supabase.table("teams").select("id, code, name, stats").execute().data
    print(f"  {len(teams)} equipos en Supabase.\n")

    updated = 0
    not_found: list[str] = []

    for team in teams:
        code = team["code"]
        name = team["name"]
        existing: dict = team.get("stats") or {}

        # Build candidate names to try
        candidates = [_norm(name)] + [_norm(n) for n in NAME_OVERRIDES.get(code, [])]

        row = None
        for candidate in candidates:
            if candidate in spi_lookup:
                row = spi_lookup[candidate]
                break

        if row is None:
            not_found.append(f"{name} ({code})")
            continue

        # Read off/def columns (FiveThirtyEight uses 'def' as column header)
        try:
            off_val = float(row.get("off") or row.get("off_rating") or 0)
            # csv.DictReader keeps column name as-is; 'def' is valid dict key
            def_val = float(row.get("def") or row.get("def_rating") or 0)
            spi_val = float(row.get("spi") or row.get("spi_rating") or 0)
        except (ValueError, TypeError):
            not_found.append(f"{name} ({code}) [error de parseo]")
            continue

        if off_val == 0 and def_val == 0:
            not_found.append(f"{name} ({code}) [valores 0]")
            continue

        merged = {
            **existing,
            "xg_for_avg": round(off_val, 3),
            "xg_against_avg": round(def_val, 3),
            "spi_rating": round(spi_val, 1),
        }

        supabase.table("teams").update({"stats": merged}).eq("code", code).execute()
        updated += 1
        print(f"  {name:25s} ({code})  off={off_val:.2f}  def={def_val:.2f}  spi={spi_val:.1f}")

    print(f"\nSPI importado: {updated}/{len(teams)} equipos actualizados.")
    if not_found:
        print(f"No encontrados en SPI ({len(not_found)}): {', '.join(not_found)}")

    print("\nPROXIMO PASO: borra el cache de predicciones y reinicia el backend.")
    print("  python -c \"from app.supabase_client import supabase; supabase.table('ai_predictions').delete().neq('id',0).execute(); print('Cache borrado')\"")


if __name__ == "__main__":
    asyncio.run(main())
