'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Users, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import type { GroupStanding } from '@/types';

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

export default function GroupsPage() {
  const [standings, setStandings] = React.useState<{group: string, teams: any[]}[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    async function loadGroups() {
      try {
        const letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'];
        const groupData = await Promise.all(
          letters.map(async (l) => {
            try {
              const data = await api.getGroupAnalysis(l);
              const teamsWithFlags = data.predicted_standings.map((s: any) => {
                const teamInfo = data.teams.find((t: any) => t.code === s.team_code);
                return { ...s, flag: teamInfo?.flag_emoji || '🏳️' };
              });
              return { group: l, teams: teamsWithFlags };
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
        <p className="text-text-secondary font-medium animate-pulse">Sincronizando grupos y clasificaciones de la IA...</p>
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
          <p className="text-text-secondary text-sm">12 grupos · 48 selecciones · Clasificaciones simuladas por DeepSeek</p>
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
              <div className="grid grid-cols-[1fr_30px_30px_30px_30px_35px] gap-1 text-[10px] font-semibold text-text-secondary uppercase tracking-wider mb-2 px-2">
                <span>Equipo</span>
                <span className="text-center">PJ</span>
                <span className="text-center">G</span>
                <span className="text-center">E</span>
                <span className="text-center">P</span>
                <span className="text-center">Pts</span>
              </div>

              {/* Team Rows */}
              <div className="space-y-1">
                {group.teams.map((team, idx) => {
                  const borderColor = idx < 2 ? 'border-l-success' : idx === 2 ? 'border-l-accent-amber' : 'border-l-transparent';
                  const bgColor = idx < 2 ? 'bg-success/[0.04]' : '';

                  return (
                    <div
                      key={team.team_code}
                      className={`grid grid-cols-[1fr_30px_30px_30px_30px_35px] gap-1 items-center py-2 px-2 rounded-lg border-l-2 ${borderColor} ${bgColor} hover:bg-bg-tertiary/40 transition-colors`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-base flex-shrink-0">{team.flag}</span>
                        <span className="text-sm font-medium text-text-primary truncate">{team.team_name}</span>
                      </div>
                      <span className="text-xs text-text-secondary text-center">{team.played}</span>
                      <span className="text-xs text-text-secondary text-center">{team.won}</span>
                      <span className="text-xs text-text-secondary text-center">{team.drawn}</span>
                      <span className="text-xs text-text-secondary text-center">{team.lost}</span>
                      <span className="text-sm font-bold text-text-primary text-center">{team.points}</span>
                    </div>
                  );
                })}
              </div>

              {/* Goal difference row */}
              <div className="mt-3 pt-3 border-t border-white/5">
                <div className="flex items-center justify-between text-[10px] text-text-secondary px-2">
                  {group.teams.map((team) => (
                    <span key={team.team_code} className="flex items-center gap-1">
                      <span>{team.flag}</span>
                      <span className={team.goal_difference > 0 ? 'text-success' : team.goal_difference < 0 ? 'text-danger' : 'text-text-secondary'}>
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
        className="flex items-center gap-6 text-xs text-text-secondary justify-center pt-4"
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
      </motion.div>
    </div>
  );
}
