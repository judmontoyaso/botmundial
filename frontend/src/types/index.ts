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
  predicted_home_score: number;
  predicted_away_score: number;
  confidence: number;
  notes: string | null;
  points_earned: number | null;
  created_at: string;
}

export interface MatchInner {
  id: number;
  match_number: number;
  stage: string;
  group_letter: string | null;
  home_team_code: string;
  away_team_code: string;
  match_date: string;
  venue: string;
  city: string;
  home_score: number | null;
  away_score: number | null;
  status: string;
}

export interface MatchWithTeams {
  match: MatchInner;
  home_team_name: string;
  away_team_name: string;
  home_team_flag: string;
  away_team_flag: string;
  home_team_flag_url?: string;
  away_team_flag_url?: string;
  home_team_ranking: number;
  away_team_ranking: number;
}

export interface AIPrediction {
  match_id: number;
  home_team_name?: string;
  away_team_name?: string;
  home_flag?: string;
  away_flag?: string;
  predicted_home_score: number;
  predicted_away_score: number;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  confidence_score: number;
  analysis_text: string;
  factors: string[];
  date?: string;
  poisson_home_lambda?: number;
  poisson_away_lambda?: number;
  scoreline_matrix?: number[][];
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
  matches_played: number;
  exact_scores: number;
  correct_outcomes: number;
  wrong: number;
  total_points: number;
  accuracy_pct: number;
  avg_confidence: number;
}
