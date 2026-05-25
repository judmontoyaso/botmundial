import type { Team, Match, MyPrediction, AIPrediction, GroupStanding } from '@/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }

  const json = await res.json();
  return json.data !== undefined ? json.data as Promise<T> : json as Promise<T>;
}

export const api = {
  // Teams
  getTeams: () => fetchJSON<Team[]>('/teams'),
  getTeam: (code: string) => fetchJSON<Team>(`/teams/${code}`),
  getTeamsByGroup: (letter: string) => fetchJSON<Team[]>(`/teams/group/${letter}`),

  // Matches
  getMatches: () => fetchJSON<Match[]>('/matches'),
  getMatch: (id: number) => fetchJSON<Match>(`/matches/${id}`),
  getUpcomingMatches: () => fetchJSON<Match[]>('/matches/upcoming'),
  updateMatchResult: (id: number, homeScore: number, awayScore: number) =>
    fetchJSON<Match>(`/matches/${id}/result`, {
      method: 'PUT',
      body: JSON.stringify({ home_score: homeScore, away_score: awayScore }),
    }),

  // Predictions
  getPredictions: () => fetchJSON<MyPrediction[]>('/predictions'),
  getPredictionStats: () => fetchJSON<any>('/predictions/stats'),
  savePrediction: (prediction: {
    match_id: number;
    predicted_home: number;
    predicted_away: number;
    notes?: string;
  }) =>
    fetchJSON<MyPrediction>('/predictions', {
      method: 'POST',
      body: JSON.stringify(prediction),
    }),

  // AI Predictions
  getAIPrediction: (matchId: number) => fetchJSON<AIPrediction>(`/predictions/ai/${matchId}`),

  // Analysis
  getMatchAnalysis: (matchId: number) => fetchJSON<any>(`/analysis/match/${matchId}`),
  getTeamAnalysis: (code: string) => fetchJSON<any>(`/analysis/team/${code}`),
  getGroupAnalysis: (letter: string) => fetchJSON<any>(`/analysis/group/${letter}`),
};
