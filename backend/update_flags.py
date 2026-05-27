"""
Store flag image URLs (flagcdn.com) in Supabase teams.stats.flag_url.

Run this once to persist flag URLs in the DB.
The backend already derives them dynamically from FIFA codes, so this
script is optional — it lets you override or inspect the URLs.
"""
import os
import sys
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

FIFA_TO_ISO2: dict[str, str] = {
    "MEX": "mx", "USA": "us", "CAN": "ca", "CRC": "cr", "PAN": "pa",
    "HON": "hn", "JAM": "jm", "HAI": "ht", "CUW": "cw", "TRI": "tt",
    "SLV": "sv", "GUA": "gt",
    "BRA": "br", "ARG": "ar", "COL": "co", "URU": "uy", "ECU": "ec",
    "CHI": "cl", "BOL": "bo", "PAR": "py", "PER": "pe", "VEN": "ve",
    "FRA": "fr", "ENG": "gb-eng", "ESP": "es", "GER": "de", "POR": "pt",
    "NED": "nl", "BEL": "be", "ITA": "it", "CRO": "hr", "SUI": "ch",
    "AUT": "at", "TUR": "tr", "SCO": "gb-sct", "ALB": "al", "SRB": "rs",
    "SVN": "si", "HUN": "hu", "ROU": "ro", "SVK": "sk", "UKR": "ua",
    "CZE": "cz", "BIH": "ba", "GRE": "gr", "NOR": "no", "SWE": "se",
    "DEN": "dk", "POL": "pl",
    "JPN": "jp", "KOR": "kr", "AUS": "au", "IRN": "ir", "KSA": "sa",
    "JOR": "jo", "QAT": "qa", "IRQ": "iq", "UZB": "uz",
    "MAR": "ma", "EGY": "eg", "NGA": "ng", "CMR": "cm", "SEN": "sn",
    "CIV": "ci", "GHA": "gh", "TUN": "tn", "ALG": "dz", "RSA": "za",
    "DRC": "cd", "COD": "cd", "MLI": "ml", "CPV": "cv", "SDN": "sd",
    "NZL": "nz",
}


def flag_url(code: str) -> str:
    iso2 = FIFA_TO_ISO2.get(code.upper(), code[:2].lower())
    return f"https://flagcdn.com/w40/{iso2}.png"


def main() -> None:
    teams = supabase.table("teams").select("id, code, name, stats").execute().data
    print(f"{len(teams)} equipos en Supabase.\n")

    updated = 0
    for team in teams:
        code = team["code"]
        existing: dict = team.get("stats") or {}
        url = flag_url(code)
        merged = {**existing, "flag_url": url}
        supabase.table("teams").update({"stats": merged}).eq("code", code).execute()
        updated += 1
        print(f"  {team['name']:25s} ({code})  {url}")

    print(f"\n{updated} equipos actualizados con flag_url.")
    print("El backend también las deriva automáticamente del código FIFA.")


if __name__ == "__main__":
    main()
