import asyncio
import json
import sys
import os

# Add the backend directory to sys.path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.team import Team, TeamStats
from app.services.llm_service import predict_match, analyze_match

def test_deepseek():
    # Create some mock teams for the test
    mexico = Team(
        id=1,
        name="Mexico",
        code="MEX",
        group_letter="A",
        fifa_ranking=15,
        confederation="CONCACAF",
        flag_emoji="🇲🇽",
        stats=TeamStats(
            goals_scored_avg=1.5,
            goals_conceded_avg=1.0,
            wins_last_10=6,
            draws_last_10=2,
            losses_last_10=2,
            world_cup_appearances=17,
            best_finish="Quarter-finals"
        )
    )

    cameroon = Team(
        id=2,
        name="Cameroon",
        code="CMR",
        group_letter="A",
        fifa_ranking=42,
        confederation="CAF",
        flag_emoji="🇨🇲",
        stats=TeamStats(
            goals_scored_avg=1.1,
            goals_conceded_avg=1.3,
            wins_last_10=4,
            draws_last_10=3,
            losses_last_10=3,
            world_cup_appearances=8,
            best_finish="Quarter-finals"
        )
    )

    stat_prediction = {
        "predicted_home_score": 2,
        "predicted_away_score": 1,
        "confidence": 0.65
    }

    print("========================================")
    print("TESTING DEEPSEEK API: PREDICT MATCH (JSON)")
    print("========================================")
    prediction = predict_match(mexico, cameroon, stat_prediction)
    print(json.dumps(prediction, indent=2))
    
    print("\n========================================")
    print("TESTING DEEPSEEK API: ANALYZE MATCH (TEXT)")
    print("========================================")
    analysis = analyze_match(mexico, cameroon, stat_prediction)
    print(analysis)

if __name__ == "__main__":
    test_deepseek()
