export interface Team {
  code: string;
  name: string;
  group: string;
  flag: string;
  fifa_ranking: number;
  confederation: string;
  stats: TeamStats;
}

export interface TeamStats {
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
}

export type MatchStatus = 'scheduled' | 'live' | 'finished' | 'postponed';
export type MatchStage = 'group' | 'round_of_32' | 'round_of_16' | 'quarter_final' | 'semi_final' | 'third_place' | 'final';

export interface Match {
  id: number;
  home_team: string;
  away_team: string;
  home_team_name: string;
  away_team_name: string;
  home_flag: string;
  away_flag: string;
  home_score: number | null;
  away_score: number | null;
  date: string;
  time: string;
  venue: string;
  city: string;
  group: string | null;
  stage: MatchStage;
  status: MatchStatus;
  matchday: number;
}

export interface MyPrediction {
  id: number;
  match_id: number;
  home_team_name: string;
  away_team_name: string;
  home_flag: string;
  away_flag: string;
  predicted_home: number;
  predicted_away: number;
  actual_home: number | null;
  actual_away: number | null;
  points: number | null;
  notes: string;
  created_at: string;
}

export interface AIPrediction {
  match_id: number;
  home_team_name: string;
  away_team_name: string;
  home_flag: string;
  away_flag: string;
  predicted_home: number;
  predicted_away: number;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  confidence: number;
  analysis: string;
  factors: AnalysisFactor[];
  date: string;
}

export interface AnalysisFactor {
  name: string;
  impact: 'positive' | 'negative' | 'neutral';
  description: string;
  team: string;
}

export interface GroupStanding {
  group: string;
  teams: GroupTeamRow[];
}

export interface GroupTeamRow {
  position: number;
  team_code: string;
  team_name: string;
  flag: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
}

export interface PredictionStats {
  total_predictions: number;
  exact_scores: number;
  correct_winner: number;
  wrong: number;
  total_points: number;
  accuracy: number;
  points_history: PointsHistoryEntry[];
}

export interface PointsHistoryEntry {
  matchday: number;
  points: number;
  cumulative: number;
}
