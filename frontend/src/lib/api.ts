import type { Team, MatchWithTeams, MyPrediction, AIPrediction, PredictionStats } from '@/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

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
  getMatches: (params?: { stage?: string; group?: string; status?: string }) => {
    const qs = params ? '?' + new URLSearchParams(Object.entries(params).filter(([, v]) => v != null) as [string, string][]).toString() : '';
    return fetchJSON<MatchWithTeams[]>(`/matches${qs}`);
  },
  getMatch: (id: number) => fetchJSON<MatchWithTeams>(`/matches/${id}`),
  getUpcomingMatches: (limit = 20) => fetchJSON<MatchWithTeams[]>(`/matches/upcoming?limit=${limit}`),
  updateMatchResult: (id: number, homeScore: number, awayScore: number) =>
    fetchJSON<MatchWithTeams>(`/matches/${id}/result`, {
      method: 'PUT',
      body: JSON.stringify({ home_score: homeScore, away_score: awayScore }),
    }),

  // Predictions
  getPredictions: () => fetchJSON<MyPrediction[]>('/predictions'),
  getPredictionStats: () => fetchJSON<PredictionStats>('/predictions/stats'),
  savePrediction: (prediction: {
    match_id: number;
    predicted_home_score: number;
    predicted_away_score: number;
    confidence?: number;
    notes?: string;
  }) =>
    fetchJSON<MyPrediction>('/predictions', {
      method: 'POST',
      body: JSON.stringify(prediction),
    }),

  deletePrediction: (id: number) =>
    fetch(`${BASE_URL}/predictions/${id}`, { method: 'DELETE' }).then(r => {
      if (!r.ok) throw new Error(`API Error: ${r.status}`);
    }),

  // AI Predictions
  getAIPrediction: (matchId: number, force = false) =>
    fetchJSON<AIPrediction>(`/predictions/ai/${matchId}${force ? '?force=true' : ''}`),

  // Analysis
  getMatchAnalysis: (matchId: number) => fetchJSON<any>(`/analysis/match/${matchId}`),
  getTeamAnalysis: (code: string) => fetchJSON<any>(`/analysis/team/${code}`),
  getGroupAnalysis: (letter: string) => fetchJSON<any>(`/analysis/group/${letter}`),
  getTournamentSimulation: (n = 5000) => fetchJSON<any>(`/analysis/tournament/simulation?n=${n}`),

  // Player absences
  getTeamAbsences: (code: string) => fetchJSON<any>(`/teams/${code}/absences`),
  addTeamAbsence: (code: string, data: { player_name: string; position?: string; importance?: number; reason?: string }) =>
    fetchJSON<any>(`/teams/${code}/absences`, { method: 'POST', body: JSON.stringify(data) }),
  deleteAbsence: (id: number) =>
    fetch(`${BASE_URL}/teams/absences/${id}`, { method: 'DELETE' }).then(r => {
      if (!r.ok) throw new Error(`API Error: ${r.status}`);
    }),
};
