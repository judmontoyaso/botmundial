"""DeepSeek LLM integration for intelligent match analysis."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.config import get_settings
from app.models.team import Team
from app.models.match import Match

logger = logging.getLogger(__name__)

_cache: dict[str, Any] = {}
_client: Any = None


def _get_client() -> Any:
    global _client
    if _client is not None:
        return _client
    settings = get_settings()
    if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY.startswith("your_"):
        logger.warning("DEEPSEEK_API_KEY not configured – LLM features will use statistical fallback.")
        return None
    try:
        from openai import OpenAI
        _client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        logger.info("DeepSeek client initialised (model: %s).", settings.DEEPSEEK_MODEL)
        return _client
    except Exception as exc:
        logger.error("Failed to initialise DeepSeek client: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_PREDICTION_PROMPT = """Eres un modelo experto en predicción de fútbol para el FIFA Mundial 2026.

Predice el resultado de {home_name} vs {away_name} en {city} ({climate_desc}).

DATOS DEL EQUIPO LOCAL — {home_name}:
  ELO: {home_elo} | FIFA #{home_ranking} | Confederación: {home_confed}
  Forma (últimos 10): {home_form} | Últimos 5: {home_form5} victorias
  xG anotados/partido: {home_xg_for} | xG concedidos/partido: {home_xg_against}
  Porterías imbatidas (últ. 10): {home_clean_sheets}
  Apariciones en Mundiales: {home_appearances} | Mejor resultado: {home_best}
  Modificador climático: {home_climate_mod:+.0%} | Ventaja continental: {home_cont_mod:+.0%}

DATOS DEL EQUIPO VISITANTE — {away_name}:
  ELO: {away_elo} | FIFA #{away_ranking} | Confederación: {away_confed}
  Forma (últimos 10): {away_form} | Últimos 5: {away_form5} victorias
  xG anotados/partido: {away_xg_for} | xG concedidos/partido: {away_xg_against}
  Porterías imbatidas (últ. 10): {away_clean_sheets}
  Apariciones en Mundiales: {away_appearances} | Mejor resultado: {away_best}
  Modificador climático: {away_climate_mod:+.0%} | Ventaja continental: {away_cont_mod:+.0%}

MODELO ESTADÍSTICO POISSON:
  λ goles esperados local: {lambda_home:.3f}
  λ goles esperados visitante: {lambda_away:.3f}
  Marcador más probable (Poisson): {stat_home_score}-{stat_away_score}
  Probabilidades: Local {stat_home_win:.0%} | Empate {stat_draw:.0%} | Visitante {stat_away_win:.0%}
  Diferencia ELO: {elo_diff:+d} a favor de {elo_advantage}

Con base en todos estos datos, razona sobre:
1. Cómo los xG revelan la calidad real de ataque y defensa
2. El impacto del clima/altitud de {city} en el rendimiento físico
3. La diferencia ELO como indicador de calidad histórica acumulada
4. La forma reciente (últimos 5) como señal del momento actual
5. Si el marcador Poisson es realista o hay factores que lo corrijan

Devuelve ÚNICAMENTE JSON válido (sin markdown) en este formato exacto:
{{
  "predicted_home_score": <entero>,
  "predicted_away_score": <entero>,
  "home_win_prob": <float 0-1>,
  "draw_prob": <float 0-1>,
  "away_win_prob": <float 0-1>,
  "confidence_score": <float 0-1>,
  "analysis_text": "<2-4 oraciones en español: táctica, clima, xG vs ELO, y apuesta recomendada>",
  "factors": [
    "<factor 1 en español>",
    "<factor 2 en español>",
    "<factor 3 en español>",
    "<factor 4 en español>"
  ]
}}
"""

_ANALYSIS_PROMPT = """Eres un analista experto de fútbol para el FIFA Mundial 2026.

Proporciona un análisis previo al partido de {home_name} vs {away_name} en {city} ({climate_desc}).

MÉTRICAS CLAVE:
- ELO: {home_name} {home_elo} vs {away_name} {away_elo} (diferencia: {elo_diff:+d})
- xG por partido: {home_name} ataca {home_xg_for} / defiende {home_xg_against} | {away_name} ataca {away_xg_for} / defiende {away_xg_against}
- Forma últimos 5: {home_name} {home_form5}/5 victorias | {away_name} {away_form5}/5 victorias
- Porterías imbatidas (últ. 10): {home_name} {home_clean_sheets} | {away_name} {away_clean_sheets}
- λ Poisson: local {lambda_home:.3f} goles esperados / visitante {lambda_away:.3f} goles esperados
- Predicción estadística: {stat_home_score}-{stat_away_score} (confianza {stat_confidence:.0%})

Escribe un análisis en español de 250-350 palabras que cubra:
1. Comparación táctica usando los datos xG (¿quién ataca mejor, quién defiende mejor?)
2. Impacto real del clima/altitud de {city} sobre los equipos según su confederación
3. Historial mundialista y experiencia en torneos de presión
4. Cómo los λ Poisson se traducen en marcadores esperados y cuál es la apuesta más segura para la polla
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_match(home: Team, away: Team, stat_prediction: dict) -> str:
    cache_key = f"analysis_{home.code}_{away.code}"
    if cache_key in _cache:
        return _cache[cache_key]

    elo_diff = home.stats.elo_rating - away.stats.elo_rating
    prompt = _ANALYSIS_PROMPT.format(
        home_name=home.name,
        away_name=away.name,
        city=stat_prediction.get("city", ""),
        climate_desc=stat_prediction.get("climate_desc", ""),
        home_elo=home.stats.elo_rating,
        away_elo=away.stats.elo_rating,
        elo_diff=elo_diff,
        home_xg_for=home.stats.xg_for_avg,
        home_xg_against=home.stats.xg_against_avg,
        away_xg_for=away.stats.xg_for_avg,
        away_xg_against=away.stats.xg_against_avg,
        home_form5=home.stats.form_last_5,
        away_form5=away.stats.form_last_5,
        home_clean_sheets=home.stats.clean_sheets_last_10,
        away_clean_sheets=away.stats.clean_sheets_last_10,
        lambda_home=stat_prediction.get("poisson_home_lambda", 1.2),
        lambda_away=stat_prediction.get("poisson_away_lambda", 1.2),
        stat_home_score=stat_prediction.get("predicted_home_score", 0),
        stat_away_score=stat_prediction.get("predicted_away_score", 0),
        stat_confidence=stat_prediction.get("confidence", 0.5),
    )
    client = _get_client()
    if client is None:
        result = _fallback_analysis(home, away, stat_prediction)
        _cache[cache_key] = result
        return result
    try:
        response = client.chat.completions.create(
            model=get_settings().DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        text = response.choices[0].message.content.strip()
        _cache[cache_key] = text
        return text
    except Exception as exc:
        logger.error("DeepSeek analysis failed: %s", exc)
        result = _fallback_analysis(home, away, stat_prediction)
        _cache[cache_key] = result
        return result


def predict_match(
    home: Team,
    away: Team,
    stat_prediction: dict,
    match: Optional[Match] = None,
    news_context: str = "",
) -> dict:
    cache_key = f"prediction_{home.code}_{away.code}_{match.id if match else 0}"
    if cache_key in _cache and not news_context:
        return _cache[cache_key]

    elo_diff = home.stats.elo_rating - away.stats.elo_rating
    elo_advantage = home.name if elo_diff >= 0 else away.name

    prompt = _PREDICTION_PROMPT.format(
        home_name=home.name,
        away_name=away.name,
        city=stat_prediction.get("city", ""),
        climate_desc=stat_prediction.get("climate_desc", ""),
        home_elo=home.stats.elo_rating,
        home_ranking=home.fifa_ranking,
        home_confed=home.confederation,
        home_form=f"{home.stats.wins_last_10}V-{home.stats.draws_last_10}E-{home.stats.losses_last_10}D",
        home_form5=home.stats.form_last_5,
        home_xg_for=home.stats.xg_for_avg,
        home_xg_against=home.stats.xg_against_avg,
        home_clean_sheets=home.stats.clean_sheets_last_10,
        home_appearances=home.stats.world_cup_appearances,
        home_best=home.stats.best_finish,
        home_climate_mod=stat_prediction.get("home_climate_mod", 0.0),
        home_cont_mod=stat_prediction.get("home_cont_mod", 0.0),
        away_elo=away.stats.elo_rating,
        away_ranking=away.fifa_ranking,
        away_confed=away.confederation,
        away_form=f"{away.stats.wins_last_10}V-{away.stats.draws_last_10}E-{away.stats.losses_last_10}D",
        away_form5=away.stats.form_last_5,
        away_xg_for=away.stats.xg_for_avg,
        away_xg_against=away.stats.xg_against_avg,
        away_clean_sheets=away.stats.clean_sheets_last_10,
        away_appearances=away.stats.world_cup_appearances,
        away_best=away.stats.best_finish,
        away_climate_mod=stat_prediction.get("away_climate_mod", 0.0),
        away_cont_mod=stat_prediction.get("away_cont_mod", 0.0),
        lambda_home=stat_prediction.get("poisson_home_lambda", 1.2),
        lambda_away=stat_prediction.get("poisson_away_lambda", 1.2),
        stat_home_score=stat_prediction.get("predicted_home_score", 0),
        stat_away_score=stat_prediction.get("predicted_away_score", 0),
        stat_home_win=stat_prediction.get("home_win_prob", 0.4),
        stat_draw=stat_prediction.get("draw_prob", 0.25),
        stat_away_win=stat_prediction.get("away_win_prob", 0.35),
        elo_diff=elo_diff,
        elo_advantage=elo_advantage,
    )

    if news_context:
        prompt += f"\n\nCONTEXTO DE NOTICIAS RECIENTES (considera estas novedades al ajustar tu predicción):\n{news_context}\n"

    client = _get_client()
    if client is None:
        result = _fallback_prediction(home, away, stat_prediction)
        _cache[cache_key] = result
        return result
    try:
        response = client.chat.completions.create(
            model=get_settings().DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content.strip())
        _cache[cache_key] = result
        return result
    except Exception as exc:
        logger.error("DeepSeek prediction failed: %s", exc)
        result = _fallback_prediction(home, away, stat_prediction)
        _cache[cache_key] = result
        return result


# ---------------------------------------------------------------------------
# Fallbacks
# ---------------------------------------------------------------------------

def _fallback_analysis(home: Team, away: Team, stat: dict) -> str:
    elo_diff = home.stats.elo_rating - away.stats.elo_rating
    stronger = home if elo_diff >= 0 else away
    weaker = away if stronger == home else home
    lambda_h = stat.get("poisson_home_lambda", 1.2)
    lambda_a = stat.get("poisson_away_lambda", 1.2)
    return (
        f"**{home.name} vs {away.name} – Análisis Previo**\n\n"
        f"El modelo Poisson proyecta {lambda_h:.2f} goles esperados para {home.name} "
        f"y {lambda_a:.2f} para {away.name}, resultando en un marcador previsto de "
        f"{stat.get('predicted_home_score', 0)}-{stat.get('predicted_away_score', 0)}.\n\n"
        f"**{home.name}** (ELO {home.stats.elo_rating}, xG {home.stats.xg_for_avg}/{home.stats.xg_against_avg}) "
        f"llega con {home.stats.form_last_5}/5 victorias recientes y "
        f"{home.stats.clean_sheets_last_10} porterías imbatidas en los últimos 10 partidos.\n\n"
        f"**{away.name}** (ELO {away.stats.elo_rating}, xG {away.stats.xg_for_avg}/{away.stats.xg_against_avg}) "
        f"suma {away.stats.form_last_5}/5 victorias en sus últimos 5. "
        f"La diferencia ELO de {abs(elo_diff)} puntos favorece a **{stronger.name}**.\n\n"
        f"**Predicción:** {stat.get('predicted_home_score', 0)}-{stat.get('predicted_away_score', 0)} "
        f"con una confianza del {stat.get('confidence', 0.5):.0%}."
    )


def _fallback_prediction(home: Team, away: Team, stat: dict) -> dict:
    elo_diff = home.stats.elo_rating - away.stats.elo_rating
    return {
        "predicted_home_score": stat.get("predicted_home_score", 0),
        "predicted_away_score": stat.get("predicted_away_score", 0),
        "home_win_prob": stat.get("home_win_prob", 0.4),
        "draw_prob": stat.get("draw_prob", 0.25),
        "away_win_prob": stat.get("away_win_prob", 0.35),
        "confidence_score": stat.get("confidence", 0.5),
        "analysis_text": (
            f"Modelo Poisson: {home.name} (ELO {home.stats.elo_rating}, xG {home.stats.xg_for_avg}) "
            f"vs {away.name} (ELO {away.stats.elo_rating}, xG {away.stats.xg_for_avg}). "
            f"Diferencia ELO {abs(elo_diff):+d}. "
            f"Marcador esperado: {stat.get('predicted_home_score', 0)}-{stat.get('predicted_away_score', 0)}."
        ),
        "factors": [
            f"ELO: {home.name} {home.stats.elo_rating} vs {away.name} {away.stats.elo_rating} (Δ{elo_diff:+d})",
            f"xG ataque: {home.name} {home.stats.xg_for_avg} vs {away.name} {away.stats.xg_for_avg}",
            f"xG defensa: {home.name} {home.stats.xg_against_avg} vs {away.name} {away.stats.xg_against_avg}",
            f"Forma reciente (últ. 5): {home.name} {home.stats.form_last_5}/5 vs {away.name} {away.stats.form_last_5}/5",
        ],
    }
