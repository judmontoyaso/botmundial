"""
Fetch latest football news for any team via Google News RSS.
Saves to cache/news/{CODE}_{YYYY-MM-DD}.json

Usage:
  python fetch_news.py CPA RYO
  python fetch_news.py ARG --lang es
  python fetch_news.py --list-cached
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

import httpx

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
NEWS_CACHE_DIR = Path(__file__).parent / "cache" / "news"
NEWS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_TTL_HOURS = 6          # re-fetch after 6 hours
MAX_HEADLINES = 8            # headlines per team
REQUEST_TIMEOUT = 10         # seconds

# Team name overrides for better Google News search results
_SEARCH_OVERRIDES: dict[str, str] = {
    "CPA": "Crystal Palace FC",
    "RYO": "Rayo Vallecano",
    "ARS": "Arsenal FC",
    "LIV": "Liverpool FC",
    "MCI": "Manchester City",
    "MUN": "Manchester United",
    "CHE": "Chelsea FC",
    "TOT": "Tottenham Hotspur",
    "FCB": "Bayern Munich",
    "BVB": "Borussia Dortmund",
    "BAR": "FC Barcelona",
    "RMA": "Real Madrid",
    "ATM": "Atletico Madrid",
    "JUV": "Juventus",
    "INT": "Inter Milan",
    # National teams
    "MEX": "Mexico seleccion futbol",
    "USA": "USMNT soccer",
    "ARG": "Argentina seleccion futbol",
    "BRA": "Brasil seleccion futbol",
    "FRA": "France equipe nationale football",
    "ESP": "Espana seleccion futbol",
    "GER": "Germany Nationalmannschaft football",
    "ENG": "England national football team",
    "POR": "Portugal seleccion futbol",
    "MAR": "Marruecos seleccion futbol",
}


def _cache_path(code: str, date_str: str) -> Path:
    return NEWS_CACHE_DIR / f"{code.upper()}_{date_str}.json"


def _load_cached(code: str) -> dict | None:
    """Return cached news if still fresh (< CACHE_TTL_HOURS old)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = _cache_path(code, today)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    fetched = datetime.fromisoformat(data.get("fetched_at", "2000-01-01T00:00:00+00:00"))
    if datetime.now(timezone.utc) - fetched > timedelta(hours=CACHE_TTL_HOURS):
        return None
    return data


def _save_cache(code: str, data: dict) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = _cache_path(code, today)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _rss_url(query: str, lang: str = "en") -> str:
    import urllib.parse
    q = urllib.parse.quote(query + " football")
    region = "GB" if lang == "en" else "ES"
    lang_code = f"{lang}-{region}"
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={region}&ceid={lang_code}"


def fetch_news(code: str, team_name: str, lang: str = "en", force: bool = False) -> dict:
    """Fetch and cache news for a team. Returns the cached/fresh data dict."""
    if not force:
        cached = _load_cached(code)
        if cached:
            return cached

    search_term = _SEARCH_OVERRIDES.get(code.upper(), team_name)
    url = _rss_url(search_term, lang)

    headlines: list[dict] = []
    try:
        resp = httpx.get(url, timeout=REQUEST_TIMEOUT, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; ProMundial/1.0)"})
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        channel = root.find("channel")
        if channel is not None:
            for item in channel.findall("item")[:MAX_HEADLINES]:
                title = (item.findtext("title") or "").strip()
                pub = (item.findtext("pubDate") or "").strip()
                source_el = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
                source = ""
                # Google News encodes source name in title as "Title - Source"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source = parts[1].strip()
                headlines.append({"title": title, "source": source, "published": pub})
    except Exception as exc:
        print(f"  [WARN] No se pudo obtener noticias para {team_name}: {exc}")

    data = {
        "team": team_name,
        "code": code.upper(),
        "search_term": search_term,
        "lang": lang,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "headlines": headlines,
    }
    if headlines:
        _save_cache(code, data)
    return data


def format_news_for_prompt(news_data: dict) -> str:
    """Return a compact string suitable for injection into a DeepSeek prompt."""
    if not news_data.get("headlines"):
        return ""
    lines = [f"Noticias recientes de {news_data['team']} (últimas {CACHE_TTL_HOURS}h):"]
    for h in news_data["headlines"]:
        src = f" ({h['source']})" if h["source"] else ""
        lines.append(f"  - {h['title']}{src}")
    return "\n".join(lines)


def get_team_news_context(home_code: str, home_name: str,
                          away_code: str, away_name: str,
                          lang: str = "en", force: bool = False) -> str:
    """Fetch news for both teams and return a combined context string."""
    home_news = fetch_news(home_code, home_name, lang=lang, force=force)
    away_news = fetch_news(away_code, away_name, lang=lang, force=force)

    parts = []
    home_ctx = format_news_for_prompt(home_news)
    away_ctx = format_news_for_prompt(away_news)
    if home_ctx:
        parts.append(home_ctx)
    if away_ctx:
        parts.append(away_ctx)
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch football news and cache as JSON")
    parser.add_argument("codes", nargs="*", help="Team codes (CPA, RYO, ARG, ...)")
    parser.add_argument("--lang", default="en", choices=["en", "es"], help="Language for search (default: en)")
    parser.add_argument("--force", action="store_true", help="Ignore cache and re-fetch")
    parser.add_argument("--list-cached", action="store_true", help="List all cached news files")
    args = parser.parse_args()

    if args.list_cached:
        files = sorted(NEWS_CACHE_DIR.glob("*.json"))
        if not files:
            print("No cached news files.")
        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            n = len(data.get("headlines", []))
            print(f"  {f.name:35s}  {n} titulares  ({data.get('fetched_at', '')[:16]})")
        return

    if not args.codes:
        parser.print_help()
        return

    # Resolve team names (check Supabase for national teams, clubs from predict_custom_match)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from predict_custom_match import _CLUBS

    for code in args.codes:
        code = code.upper()
        if code in _CLUBS:
            name = _CLUBS[code]["name"]
        else:
            try:
                from app.services import data_service
                team = data_service.get_team_by_code(code)
                name = team.name if team else code
            except Exception:
                name = code

        print(f"\nFetching news: {name} ({code}) [{args.lang}] ...")
        data = fetch_news(code, name, lang=args.lang, force=args.force)
        headlines = data.get("headlines", [])
        if not headlines:
            print("  Sin titulares encontrados.")
        else:
            for h in headlines:
                src = f"  [{h['source']}]" if h["source"] else ""
                print(f"  * {h['title']}{src}")
            print(f"\n  -> Guardado en cache/news/{code}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json")


if __name__ == "__main__":
    main()
