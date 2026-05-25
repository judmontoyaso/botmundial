"""DeepSeek LLM integration for intelligent match analysis."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.config import get_settings
from app.models.team import Team
from app.models.match import Match

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory cache  { cache_key: response_dict }
# ---------------------------------------------------------------------------
_cache: dict[str, Any] = {}

# ---------------------------------------------------------------------------
# DeepSeek client initialisation
# ---------------------------------------------------------------------------
_client: Any = None


def _get_client() -> Any:
    """Lazily initialise the OpenAI client for DeepSeek."""
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY.startswith("your_"):
        logger.warning("DEEPSEEK_API_KEY not configured – LLM features will use fallbacks.")
        return None

    try:
        from openai import OpenAI

        _client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
        )
        logger.info("DeepSeek client initialised successfully.")
        return _client
    except Exception as exc:
        logger.error("Failed to initialise DeepSeek client: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Prompt templates (CRISP framework)
# ---------------------------------------------------------------------------

_ANALYSIS_PROMPT = """You are an expert football analyst for the FIFA World Cup 2026.

**Context**: Provide a pre-match analysis for {home_name} vs {away_name} playing in {city} ({climate_desc}).
**Role**: Senior football analyst with deep tactical knowledge.
**Intent**: Help a prediction-pool (polla) player make an informed bet.
**Scope**: Focus on recent form, tactical matchups, key players, historical precedents, and crucially, how the specific climate/altitude of {city} and continental home advantage might physically and mentally affect the teams.
**Parameters**: Keep the analysis between 200-400 words. Be specific and data-driven. Respond in Spanish.

Team Data:
- {home_name} ({home_code}): FIFA #{home_ranking}, {home_confederation}
  Form (last 10): {home_form} | Goals: {home_goals_avg} scored, {home_conceded_avg} conceded
  World Cup pedigree: {home_appearances} appearances, {home_best}
  Climate adaptation score: {home_climate_mod} | Continental support: {home_cont_mod}
  
- {away_name} ({away_code}): FIFA #{away_ranking}, {away_confederation}
  Form (last 10): {away_form} | Goals: {away_goals_avg} scored, {away_conceded_avg} conceded
  World Cup pedigree: {away_appearances} appearances, {away_best}
  Climate adaptation score: {away_climate_mod} | Continental support: {away_cont_mod}

Statistical prediction: {stat_home_score}-{stat_away_score} (confidence: {stat_confidence})

Provide a detailed narrative analysis covering:
1. Tactical outlook and expected playing styles
2. How the climate/altitude of {city} will physically impact both teams
3. Historical context between these teams
4. Prediction and recommended bet for a polla
"""

_PREDICTION_PROMPT = """You are an expert football prediction model for the FIFA World Cup 2026.

Predict the outcome of {home_name} vs {away_name} playing in {city} ({climate_desc}).

Team Data:
- {home_name}: FIFA #{home_ranking}, Form: {home_form}, Goals: {home_goals_avg}, Climate mod: {home_climate_mod}, Cont. Support: {home_cont_mod}
- {away_name}: FIFA #{away_ranking}, Form: {away_form}, Goals: {away_goals_avg}, Climate mod: {away_climate_mod}, Cont. Support: {away_cont_mod}

Statistical model prediction: {stat_home_score}-{stat_away_score}

Return ONLY valid JSON (no markdown, no explanation) in this exact format. Ensure 'analysis_text' and 'factors' are in SPANISH:
{{
  "predicted_home_score": <int>,
  "predicted_away_score": <int>,
  "home_win_prob": <float 0-1>,
  "draw_prob": <float 0-1>,
  "away_win_prob": <float 0-1>,
  "confidence_score": <float 0-1>,
  "analysis_text": "<2-3 sentence summary covering tactics and climate influence>",
  "factors": ["<factor1>", "<factor2>", "<factor3>", "<factor4>"]
}}
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_match(
    home: Team,
    away: Team,
    stat_prediction: dict,
) -> str:
    """Generate a narrative analysis text for a match using DeepSeek."""
    cache_key = f"analysis_{home.code}_{away.code}"
    if cache_key in _cache:
        return _cache[cache_key]

    prompt = _ANALYSIS_PROMPT.format(
        home_name=home.name,
        home_code=home.code,
        home_ranking=home.fifa_ranking,
        home_confederation=home.confederation,
        home_form=f"{home.stats.wins_last_10}W-{home.stats.draws_last_10}D-{home.stats.losses_last_10}L",
        home_goals_avg=home.stats.goals_scored_avg,
        home_conceded_avg=home.stats.goals_conceded_avg,
        home_appearances=home.stats.world_cup_appearances,
        home_best=home.stats.best_finish,
        home_climate_mod=stat_prediction.get("home_climate_mod", 0),
        home_cont_mod=stat_prediction.get("home_cont_mod", 0),
        away_name=away.name,
        away_code=away.code,
        away_ranking=away.fifa_ranking,
        away_confederation=away.confederation,
        away_form=f"{away.stats.wins_last_10}W-{away.stats.draws_last_10}D-{away.stats.losses_last_10}L",
        away_goals_avg=away.stats.goals_scored_avg,
        away_conceded_avg=away.stats.goals_conceded_avg,
        away_appearances=away.stats.world_cup_appearances,
        away_best=away.stats.best_finish,
        away_climate_mod=stat_prediction.get("away_climate_mod", 0),
        away_cont_mod=stat_prediction.get("away_cont_mod", 0),
        stat_home_score=stat_prediction.get("predicted_home_score", 0),
        stat_away_score=stat_prediction.get("predicted_away_score", 0),
        stat_confidence=stat_prediction.get("confidence", 0.5),
        city=stat_prediction.get("city", "Unknown Venue"),
        climate_desc=stat_prediction.get("climate_desc", "Unknown Climate")
    )

    client = _get_client()
    if client is None:
        fallback = _fallback_analysis(home, away, stat_prediction)
        _cache[cache_key] = fallback
        return fallback

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = response.choices[0].message.content.strip()
        _cache[cache_key] = text
        return text
    except Exception as exc:
        logger.error("DeepSeek analysis failed: %s", exc)
        fallback = _fallback_analysis(home, away, stat_prediction)
        _cache[cache_key] = fallback
        return fallback


def predict_match(
    home: Team,
    away: Team,
    stat_prediction: dict,
    match: Optional[Match] = None
) -> dict:
    """Get structured prediction JSON from DeepSeek."""
    cache_key = f"prediction_{home.code}_{away.code}_{match.id if match else 0}"
    if cache_key in _cache:
        return _cache[cache_key]

    prompt = _PREDICTION_PROMPT.format(
        home_name=home.name,
        home_code=home.code,
        home_ranking=home.fifa_ranking,
        home_form=f"{home.stats.wins_last_10}W-{home.stats.draws_last_10}D-{home.stats.losses_last_10}L",
        home_goals_avg=home.stats.goals_scored_avg,
        home_climate_mod=stat_prediction.get("home_climate_mod", 0),
        home_cont_mod=stat_prediction.get("home_cont_mod", 0),
        away_name=away.name,
        away_code=away.code,
        away_ranking=away.fifa_ranking,
        away_form=f"{away.stats.wins_last_10}W-{away.stats.draws_last_10}D-{away.stats.losses_last_10}L",
        away_goals_avg=away.stats.goals_scored_avg,
        away_climate_mod=stat_prediction.get("away_climate_mod", 0),
        away_cont_mod=stat_prediction.get("away_cont_mod", 0),
        stat_home_score=stat_prediction.get("predicted_home_score", 0),
        stat_away_score=stat_prediction.get("predicted_away_score", 0),
        city=stat_prediction.get("city", "Unknown"),
        climate_desc=stat_prediction.get("climate_desc", "Unknown")
    )

    client = _get_client()
    if client is None:
        fallback = _fallback_prediction(home, away, stat_prediction)
        _cache[cache_key] = fallback
        return fallback

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        text = response.choices[0].message.content.strip()

        result = json.loads(text)
        _cache[cache_key] = result
        return result
    except Exception as exc:
        logger.error("DeepSeek prediction failed: %s", exc)
        fallback = _fallback_prediction(home, away, stat_prediction)
        _cache[cache_key] = fallback
        return fallback


# ---------------------------------------------------------------------------
# Fallback responses when DeepSeek is unavailable
# ---------------------------------------------------------------------------

def _fallback_analysis(home: Team, away: Team, stat: dict) -> str:
    """Generate a rule-based analysis when the LLM is not available."""
    stronger = home if home.fifa_ranking < away.fifa_ranking else away
    weaker = away if stronger == home else home
    diff = abs(home.fifa_ranking - away.fifa_ranking)

    analysis = (
        f"**{home.name} vs {away.name} – Pre-Match Analysis**\n\n"
        f"{home.name} (FIFA #{home.fifa_ranking}) face {away.name} (FIFA #{away.fifa_ranking}) "
        f"in what promises to be a {'competitive encounter' if diff < 10 else 'match where ' + stronger.name + ' hold a clear advantage'}.\n\n"
        f"**{home.name}** come into this match with a form record of "
        f"{home.stats.wins_last_10}W-{home.stats.draws_last_10}D-{home.stats.losses_last_10}L "
        f"in their last 10 matches, averaging {home.stats.goals_scored_avg} goals scored and "
        f"conceding {home.stats.goals_conceded_avg} per game. "
        f"With {home.stats.world_cup_appearances} World Cup appearances, they bring "
        f"{'considerable' if home.stats.world_cup_appearances > 10 else 'some'} tournament experience.\n\n"
        f"**{away.name}** have posted {away.stats.wins_last_10} wins from their last 10 outings, "
        f"scoring {away.stats.goals_scored_avg} goals per game while conceding {away.stats.goals_conceded_avg}. "
        f"Their World Cup pedigree reads: {away.stats.best_finish}.\n\n"
        f"**Prediction:** The statistical model favours a **{stat.get('predicted_home_score', 0)}-"
        f"{stat.get('predicted_away_score', 0)}** result with {stat.get('confidence', 0.5):.0%} confidence. "
        f"{'A home win looks the safest bet.' if stat.get('predicted_home_score', 0) > stat.get('predicted_away_score', 0) else 'The away side could spring a surprise.' if stat.get('predicted_home_score', 0) < stat.get('predicted_away_score', 0) else 'A draw is a realistic outcome.'}"
    )
    return analysis


def _fallback_prediction(home: Team, away: Team, stat: dict) -> dict:
    """Return the statistical prediction as a structured fallback."""
    return {
        "predicted_home_score": stat.get("predicted_home_score", 0),
        "predicted_away_score": stat.get("predicted_away_score", 0),
        "home_win_prob": stat.get("home_win_prob", 0.4),
        "draw_prob": stat.get("draw_prob", 0.25),
        "away_win_prob": stat.get("away_win_prob", 0.35),
        "confidence_score": stat.get("confidence", 0.5),
        "analysis_text": (
            f"Based on statistical analysis, {home.name} (FIFA #{home.fifa_ranking}) "
            f"are predicted to {'win' if stat.get('predicted_home_score', 0) > stat.get('predicted_away_score', 0) else 'draw with' if stat.get('predicted_home_score', 0) == stat.get('predicted_away_score', 0) else 'lose to'} "
            f"{away.name} (FIFA #{away.fifa_ranking}) with a predicted scoreline of "
            f"{stat.get('predicted_home_score', 0)}-{stat.get('predicted_away_score', 0)}."
        ),
        "factors": [
            f"FIFA ranking difference: {abs(home.fifa_ranking - away.fifa_ranking)} positions",
            f"{home.name} form: {home.stats.wins_last_10}W in last 10",
            f"{away.name} form: {away.stats.wins_last_10}W in last 10",
            f"Goal difference in averages: {home.stats.goals_scored_avg - away.stats.goals_scored_avg:+.1f}",
        ],
    }
