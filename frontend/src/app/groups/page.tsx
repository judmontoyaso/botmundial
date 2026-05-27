'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Users, Loader2, Zap, Shield } from 'lucide-react';
import { api } from '@/lib/api';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

interface TeamStats {
  elo_rating?: number;
  xg_for_avg?: number;
  xg_against_avg?: number;
  [key: string]: unknown;
}

interface TeamData {
  code: string;
  name: string;
  flag_emoji: string;
  fifa_ranking: number;
  confederation: string;
  stats: TeamStats;
}

interface StandingEntry {
  team_code: string;
  team_name: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  flag?: string;
  elo?: number;
  xg_for?: number;
  xg_against?: number;
  strength?: number;
}

interface GroupData {
  group: string;
  teams: StandingEntry[];
}

function ELOBadge({ elo }: { elo: number | undefined }) {
  if (!elo) return null;
  const tier =
    elo >= 2000 ? 'text-accent-gold' :
    elo >= 1850 ? 'text-accent-amber' :
    elo >= 1700 ? 'text-text-secondary' :
    'text-text-secondary/60';
  return (
    <span className={`text-[10px] font-mono font-semibold ${tier} flex-shrink-0`}>
      {elo}
    </span>
  );
}

function XGBar({ value, max = 2.0, type }: { value: number | undefined; max?: number; type: 'attack' | 'defense' }) {
  if (!value) return null;
  const pct = Math.min((value / max) * 100, 100);
  const color = type === 'attack' ? 'bg-accent-gold' : 'bg-blue-500/60';
  return (
    <div className="flex items-center gap-1.5 min-w-0">
      <div className="flex-1 h-1 bg-bg-tertiary/50 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[9px] text-text-secondary/70 tabular-nums w-6 text-right flex-shrink-0">
        {value.toFixed(1)}
      </span>
    </div>
  );
}

export default function GroupsPage() {
  const [standings, setStandings] = React.useState<GroupData[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    async function loadGroups() {
      try {
        const letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'];
        const groupData = await Promise.all(
          letters.map(async (l) => {
            try {
              const data = await api.getGroupAnalysis(l);

              // Build a quick lookup: code → team data and strength
              const teamDataMap: Record<string, TeamData> = {};
              for (const t of data.teams as TeamData[]) {
                teamDataMap[t.code] = t;
              }
              const strengthScores: Record<string, number> = data.strength_scores ?? {};

              const teamsWithMeta = (data.predicted_standings as any[]).map((s: any) => {
                const td = teamDataMap[s.team_code];
                return {
                  ...s,
                  flag: td?.flag_emoji ?? '🏳️',
                  elo: td?.stats?.elo_rating,
                  xg_for: td?.stats?.xg_for_avg,
                  xg_against: td?.stats?.xg_against_avg,
                  strength: strengthScores[s.team_code],
                };
              });

              return { group: l, teams: teamsWithMeta };
            } catch (e) {
              console.error(`Error loading group ${l}`, e);
              return { group: l, teams: [] };
            }
          })
        );
        setStandings(groupData.filter(g => g.teams.length > 0));
      } catch (error) {
        console.error('Error loading groups:', error);
      } finally {
        setLoading(false);
      }
    }
    loadGroups();
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto h-[60vh] flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-12 h-12 text-accent-gold animate-spin" />
        <p className="text-text-secondary font-medium animate-pulse">
          Calculando pronósticos con modelo Poisson + ELO...
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-3"
      >
        <div className="p-2.5 rounded-xl bg-accent-gold/10">
          <Users className="w-6 h-6 text-accent-gold" />
        </div>
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary">
            Fase de <span className="gradient-gold-text">Grupos</span>
          </h1>
          <p className="text-text-secondary text-sm">
            12 grupos · 48 selecciones · Pronóstico Poisson + ELO + xG
          </p>
        </div>
      </motion.div>

      {/* Groups Grid */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5"
      >
        {standings.map((group) => (
          <motion.div
            key={group.group}
            variants={item}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            className="rounded-2xl border border-accent-gold/10 bg-bg-secondary/60 backdrop-blur-xl overflow-hidden transition-shadow duration-300 hover:shadow-[0_0_25px_rgba(212,168,83,0.08)] hover:border-accent-gold/20"
          >
            {/* Group Header */}
            <div className="px-5 py-3.5 bg-gradient-to-r from-accent-gold/10 to-transparent border-b border-accent-gold/10">
              <h2 className="text-sm font-bold text-accent-gold tracking-wider uppercase">
                Grupo {group.group}
              </h2>
            </div>

            {/* Table */}
            <div className="p-4">
              {/* Table Header */}
              <div className="grid grid-cols-[1fr_28px_28px_28px_28px_32px] gap-1 text-[10px] font-semibold text-text-secondary uppercase tracking-wider mb-2 px-1">
                <span>Equipo</span>
                <span className="text-center">PJ</span>
                <span className="text-center">G</span>
                <span className="text-center">E</span>
                <span className="text-center">P</span>
                <span className="text-center">Pts</span>
              </div>

              {/* Team Rows */}
              <div className="space-y-0.5">
                {group.teams.map((team, idx) => {
                  const borderColor =
                    idx < 2
                      ? 'border-l-success'
                      : idx === 2
                      ? 'border-l-accent-amber'
                      : 'border-l-transparent';
                  const bgColor = idx < 2 ? 'bg-success/[0.04]' : '';

                  return (
                    <div key={team.team_code} className={`border-l-2 ${borderColor} ${bgColor} rounded-r-lg`}>
                      {/* Main row */}
                      <div className="grid grid-cols-[1fr_28px_28px_28px_28px_32px] gap-1 items-center py-1.5 px-1 hover:bg-bg-tertiary/40 transition-colors rounded-r-lg">
                        <div className="flex items-center gap-1.5 min-w-0">
                          <span className="text-base flex-shrink-0">{team.flag}</span>
                          <div className="flex flex-col min-w-0">
                            <span className="text-xs font-medium text-text-primary truncate leading-tight">
                              {team.team_name}
                            </span>
                            <ELOBadge elo={team.elo} />
                          </div>
                        </div>
                        <span className="text-[11px] text-text-secondary text-center">{team.played}</span>
                        <span className="text-[11px] text-text-secondary text-center">{team.won}</span>
                        <span className="text-[11px] text-text-secondary text-center">{team.drawn}</span>
                        <span className="text-[11px] text-text-secondary text-center">{team.lost}</span>
                        <span className="text-sm font-bold text-text-primary text-center">{team.points}</span>
                      </div>

                      {/* xG sub-row */}
                      {(team.xg_for || team.xg_against) && (
                        <div className="grid grid-cols-2 gap-2 px-2 pb-1.5">
                          <div className="flex items-center gap-1">
                            <Zap className="w-2.5 h-2.5 text-accent-gold/60 flex-shrink-0" />
                            <XGBar value={team.xg_for} type="attack" />
                          </div>
                          <div className="flex items-center gap-1">
                            <Shield className="w-2.5 h-2.5 text-blue-400/60 flex-shrink-0" />
                            <XGBar value={team.xg_against} type="defense" />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Goal difference row */}
              <div className="mt-3 pt-3 border-t border-white/5">
                <div className="flex items-center justify-between text-[10px] text-text-secondary px-1">
                  {group.teams.map((team) => (
                    <span key={team.team_code} className="flex items-center gap-0.5">
                      <span>{team.flag}</span>
                      <span
                        className={
                          team.goal_difference > 0
                            ? 'text-success'
                            : team.goal_difference < 0
                            ? 'text-danger'
                            : 'text-text-secondary'
                        }
                      >
                        {team.goal_difference > 0 ? '+' : ''}{team.goal_difference}
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Legend */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="flex flex-wrap items-center gap-x-6 gap-y-3 text-xs text-text-secondary justify-center pt-4"
      >
        <span className="flex items-center gap-2">
          <span className="w-3 h-0.5 bg-success rounded-full" />
          Clasificado
        </span>
        <span className="flex items-center gap-2">
          <span className="w-3 h-0.5 bg-accent-amber rounded-full" />
          Posible clasificación (mejor tercero)
        </span>
        <span className="flex items-center gap-2">
          <span className="w-3 h-0.5 bg-text-secondary/30 rounded-full" />
          Eliminado
        </span>
        <span className="flex items-center gap-2">
          <Zap className="w-3 h-3 text-accent-gold/60" />
          xG Ataque
        </span>
        <span className="flex items-center gap-2">
          <Shield className="w-3 h-3 text-blue-400/60" />
          xG Defensa
        </span>
      </motion.div>
    </div>
  );
}
