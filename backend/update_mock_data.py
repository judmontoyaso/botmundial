import json
import os
import sys

def main():
    # Read updated JSON data
    with open("app/data/teams.json", "r", encoding="utf-8") as f:
        teams = json.load(f)
    
    with open("app/data/schedule.json", "r", encoding="utf-8") as f:
        schedule = json.load(f)

    # Build mockTeams string
    teams_ts = "export const mockTeams: Team[] = [\n"
    for t in teams:
        teams_ts += f"  {{ code: \"{t['code']}\", name: \"{t['name']}\", group: \"{t['group_letter']}\", flag: \"{t['flag_emoji']}\", fifa_ranking: {t['fifa_ranking']}, confederation: \"{t['confederation']}\", stats: {{ played: 3, wins: {t['stats']['wins_last_10']}, draws: {t['stats']['draws_last_10']}, losses: {t['stats']['losses_last_10']}, goals_for: {int(t['stats']['goals_scored_avg']*10)}, goals_against: {int(t['stats']['goals_conceded_avg']*10)}, goal_difference: 0, points: 0 }} }},\n"
    teams_ts += "];\n"

    # Build mockMatches string
    matches_ts = "export const mockMatches: Match[] = [\n"
    for i, m in enumerate(schedule):
        # find teams
        ht = next((t for t in teams if t['code'] == m['home_team']), None)
        at = next((t for t in teams if t['code'] == m['away_team']), None)
        
        status = "scheduled"
        h_score = "null"
        a_score = "null"

        matches_ts += f"  {{ id: {m['match_number']}, home_team: \"{m['home_team']}\", away_team: \"{m['away_team']}\", home_team_name: \"{ht['name'] if ht else ''}\", away_team_name: \"{at['name'] if at else ''}\", home_flag: \"{ht['flag_emoji'] if ht else ''}\", away_flag: \"{at['flag_emoji'] if at else ''}\", home_score: {h_score}, away_score: {a_score}, date: \"{m['match_date'][:10]}\", time: \"{m['match_date'][11:16]}\", venue: \"{m['venue']}\", city: \"{m['city']}\", group: \"{m['group_letter']}\", stage: 'group', status: \"{status}\", matchday: 1 }},\n"
    matches_ts += "];\n"

    # Rest of the file can be static/unchanged or minimal
    rest_of_file = """
export const mockAIPredictions: AIPrediction[] = [
  {
    match_id: 1,
    home_team_name: 'Mexico',
    away_team_name: 'South Korea',
    home_flag: '🇲🇽',
    away_flag: '🇰🇷',
    predicted_home: 2,
    predicted_away: 1,
    home_win_prob: 0.55,
    draw_prob: 0.25,
    away_win_prob: 0.20,
    confidence: 0.70,
    analysis: 'Análisis preliminar de DeepSeek: México domina el historial reciente frente a rivales asiáticos, pero la velocidad en transición de Corea del Sur será un desafío. Se espera un partido ajustado donde el mediocampo mexicano haga la diferencia.',
    factors: [
      { name: 'Ranking', impact: 'positive', description: 'México #15 vs Corea #22', team: 'MEX' },
      { name: 'Velocidad', impact: 'negative', description: 'Corea del Sur es letal en contraataque', team: 'KOR' }
    ],
    date: '2026-06-11',
  },
  {
    match_id: 9,
    home_team_name: 'Brazil',
    away_team_name: 'Morocco',
    home_flag: '🇧🇷',
    away_flag: '🇲🇦',
    predicted_home: 3,
    predicted_away: 1,
    home_win_prob: 0.65,
    draw_prob: 0.20,
    away_win_prob: 0.15,
    confidence: 0.85,
    analysis: 'Análisis preliminar de DeepSeek: Brasil llega como uno de los máximos favoritos. Aunque Marruecos es defensivamente sólido, la calidad ofensiva de la delantera brasileña terminará rompiendo el cerco defensivo en la segunda mitad.',
    factors: [
      { name: 'Ataque', impact: 'positive', description: 'Brasil promedia 2.0 goles por partido', team: 'BRA' },
      { name: 'Defensa', impact: 'neutral', description: 'Marruecos concede muy pocos goles', team: 'MAR' }
    ],
    date: '2026-06-13',
  }
];

export const mockMyPredictions: MyPrediction[] = [];

function buildGroupStandings(): GroupStanding[] {
  const groups = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'];
  return groups.map(group => {
    const teamsInGroup = mockTeams
      .filter(t => t.group === group)
      .sort((a, b) => {
        if (b.stats.points !== a.stats.points) return b.stats.points - a.stats.points;
        if (b.stats.goal_difference !== a.stats.goal_difference) return b.stats.goal_difference - a.stats.goal_difference;
        return b.stats.goals_for - a.stats.goals_for;
      });

    return {
      group,
      teams: teamsInGroup.map((team, idx) => ({
        position: idx + 1,
        team_code: team.code,
        team_name: team.name,
        flag: team.flag,
        played: team.stats.played,
        wins: team.stats.wins,
        draws: team.stats.draws,
        losses: team.stats.losses,
        goals_for: team.stats.goals_for,
        goals_against: team.stats.goals_against,
        goal_difference: team.stats.goal_difference,
        points: team.stats.points,
      })),
    };
  });
}

export const mockGroupStandings: GroupStanding[] = buildGroupStandings();

export const mockPredictionStats: PredictionStats = {
  total_predictions: 0,
  exact_scores: 0,
  correct_winner: 0,
  wrong: 0,
  total_points: 0,
  accuracy: 0,
  points_history: [],
};

export function getUpcomingMatches(count: number = 5): Match[] {
  return mockMatches
    .filter(m => m.status === 'scheduled')
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .slice(0, count);
}
export function getFinishedMatches(): Match[] { return mockMatches.filter(m => m.status === 'finished'); }
export function getTeamByCode(code: string): Team | undefined { return mockTeams.find(t => t.code === code); }
export function getMatchesByGroup(group: string): Match[] { return mockMatches.filter(m => m.group === group); }
export function getAIPredictionForMatch(matchId: number): AIPrediction | undefined { return mockAIPredictions.find(p => p.match_id === matchId); }
"""

    full_ts = "import type { Team, Match, MyPrediction, AIPrediction, GroupStanding, PredictionStats } from '@/types';\n\n" + teams_ts + "\n" + matches_ts + "\n" + rest_of_file

    with open("../frontend/src/lib/mock-data.ts", "w", encoding="utf-8") as f:
        f.write(full_ts)

if __name__ == "__main__":
    main()
