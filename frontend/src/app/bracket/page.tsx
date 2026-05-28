'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { GitBranch, RefreshCw, TrendingUp, Award, Star } from 'lucide-react';
import { api } from '@/lib/api';
import FlagImg from '@/components/ui/FlagImg';
import LoadingBall from '@/components/ui/LoadingBall';

interface TeamSim {
  team_code: string;
  team_name: string;
  flag_emoji: string;
  elo: number;
  confederation: string;
  p_champion: number;
  p_finalist: number;
  p_top4: number;
  p_top8: number;
  p_group_advance: number;
}

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.04 } },
};
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

function ProbBar({ value, max = 100, color = 'bg-accent-gold' }: { value: number; max?: number; color?: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex items-center gap-2 min-w-0">
      <div className="flex-1 h-1.5 bg-bg-tertiary/50 rounded-full overflow-hidden">
        <motion.div
          className={`h-full ${color} rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>
      <span className="text-[11px] tabular-nums text-text-secondary w-10 text-right flex-shrink-0">
        {value.toFixed(1)}%
      </span>
    </div>
  );
}

function MedalIcon({ position }: { position: number }) {
  if (position === 1) return <span className="text-accent-gold text-base">1</span>;
  if (position === 2) return <span className="text-gray-300 text-base">2</span>;
  if (position === 3) return <span className="text-amber-600 text-base">3</span>;
  return <span className="text-text-secondary/40 text-sm">{position}</span>;
}

function ConfederationBadge({ confederation }: { confederation: string }) {
  const colors: Record<string, string> = {
    CONMEBOL: 'bg-yellow-500/10 text-yellow-400',
    UEFA: 'bg-blue-500/10 text-blue-400',
    CONCACAF: 'bg-green-500/10 text-green-400',
    CAF: 'bg-orange-500/10 text-orange-400',
    AFC: 'bg-red-500/10 text-red-400',
    OFC: 'bg-purple-500/10 text-purple-400',
  };
  return (
    <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full flex-shrink-0 ${colors[confederation] ?? 'bg-bg-tertiary text-text-secondary'}`}>
      {confederation}
    </span>
  );
}

export default function BracketPage() {
  const [teams, setTeams] = React.useState<TeamSim[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [simCount, setSimCount] = React.useState(5000);
  const [generatedAt, setGeneratedAt] = React.useState('');

  async function load(n: number, force = false) {
    try {
      const data = await api.getTournamentSimulation(n);
      setTeams(data.teams ?? []);
      setGeneratedAt(data.generated_at ?? '');
    } catch (e) {
      console.error(e);
    }
  }

  React.useEffect(() => {
    setLoading(true);
    load(simCount).finally(() => setLoading(false));
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await load(simCount, true);
    setRefreshing(false);
  };

  const top16 = teams.slice(0, 16);
  const rest = teams.slice(16);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto h-[60vh] flex flex-col items-center justify-center gap-4">
        <LoadingBall text={`Ejecutando ${simCount.toLocaleString()} simulaciones Monte Carlo...`} />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-accent-gold/10">
            <GitBranch className="w-6 h-6 text-accent-gold" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-text-primary">
              Simulación <span className="gradient-gold-text">Monte Carlo</span>
            </h1>
            <p className="text-text-secondary text-sm">
              {simCount.toLocaleString()} torneos simulados · Poisson + ELO + xG + H2H + Forma
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={simCount}
            onChange={e => setSimCount(Number(e.target.value))}
            className="px-3 py-2 rounded-xl bg-bg-secondary/60 border border-accent-gold/10 text-text-primary text-sm focus:outline-none focus:border-accent-gold/30"
          >
            <option value={1000}>1 000 sims</option>
            <option value={5000}>5 000 sims</option>
            <option value={10000}>10 000 sims</option>
          </select>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-gold/10 border border-accent-gold/20 text-accent-gold text-sm font-medium hover:bg-accent-gold/15 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Recalcular
          </button>
        </div>
      </motion.div>

      {/* Model factors badge */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex flex-wrap gap-2 text-xs"
      >
        {['xG Ataque/Defensa', 'ELO Rating', 'Forma Reciente', 'H2H Histórico', 'Ausencias', 'Clima/Altitud', 'Ventaja Continental'].map(f => (
          <span key={f} className="px-2.5 py-1 rounded-full bg-accent-gold/8 border border-accent-gold/15 text-accent-gold/80">
            {f}
          </span>
        ))}
      </motion.div>

      {/* Top 16 favorites */}
      <div>
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
          <Star className="w-4 h-4 text-accent-gold" />
          Favoritos para ganar el Mundial
        </h2>
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 gap-3"
        >
          {top16.map((team, idx) => (
            <motion.div
              key={team.team_code}
              variants={item}
              className="rounded-xl border border-accent-gold/10 bg-bg-secondary/50 backdrop-blur-xl p-4 hover:border-accent-gold/20 hover:bg-bg-secondary/70 transition-all"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-7 text-center font-bold flex-shrink-0">
                  <MedalIcon position={idx + 1} />
                </div>
                <FlagImg emoji={team.flag_emoji} teamCode={team.team_code} name={team.team_name} size="md" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-text-primary truncate">{team.team_name}</span>
                    <ConfederationBadge confederation={team.confederation} />
                  </div>
                  <span className="text-[10px] text-text-secondary font-mono">ELO {team.elo}</span>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="text-lg font-bold gradient-gold-text">{team.p_champion}%</div>
                  <div className="text-[10px] text-text-secondary">campeón</div>
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-text-secondary w-16 flex-shrink-0">Campeón</span>
                  <ProbBar value={team.p_champion} max={Math.max(...top16.map(t => t.p_champion), 1)} color="bg-accent-gold" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-text-secondary w-16 flex-shrink-0">Final</span>
                  <ProbBar value={team.p_finalist} max={100} color="bg-accent-amber/70" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-text-secondary w-16 flex-shrink-0">Top 4</span>
                  <ProbBar value={team.p_top4} max={100} color="bg-blue-400/60" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-text-secondary w-16 flex-shrink-0">Top 8</span>
                  <ProbBar value={team.p_top8} max={100} color="bg-success/50" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-text-secondary w-16 flex-shrink-0">Grupos</span>
                  <ProbBar value={team.p_group_advance} max={100} color="bg-text-secondary/30" />
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Full probability table */}
      <div>
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-accent-gold" />
          Tabla completa · 48 selecciones
        </h2>
        <div className="rounded-2xl border border-accent-gold/10 bg-bg-secondary/40 backdrop-blur-xl overflow-hidden">
          {/* Table header */}
          <div className="grid grid-cols-[2.5rem_1fr_5rem_5rem_5rem_5rem_5rem] gap-1 px-4 py-2.5 bg-bg-tertiary/20 border-b border-accent-gold/10 text-[10px] font-semibold text-text-secondary uppercase tracking-wider">
            <span>#</span>
            <span>Equipo</span>
            <span className="text-center">Campeón</span>
            <span className="text-center">Final</span>
            <span className="text-center">Top 4</span>
            <span className="text-center">Top 8</span>
            <span className="text-center">Grupos</span>
          </div>

          <motion.div variants={container} initial="hidden" animate="show">
            {teams.map((team, idx) => (
              <motion.div
                key={team.team_code}
                variants={item}
                className={`grid grid-cols-[2.5rem_1fr_5rem_5rem_5rem_5rem_5rem] gap-1 px-4 py-2.5 items-center hover:bg-bg-tertiary/20 transition-colors border-b border-white/[0.03] last:border-0 ${idx < 3 ? 'bg-accent-gold/[0.03]' : ''}`}
              >
                <span className="text-xs font-bold text-text-secondary/50 text-center">{idx + 1}</span>
                <div className="flex items-center gap-2 min-w-0">
                  <FlagImg emoji={team.flag_emoji} teamCode={team.team_code} name={team.team_name} size="sm" />
                  <div className="min-w-0">
                    <span className="text-xs font-medium text-text-primary truncate block">{team.team_name}</span>
                    <span className="text-[9px] text-text-secondary/50 font-mono">{team.elo}</span>
                  </div>
                </div>
                <span className={`text-xs font-bold text-center ${team.p_champion >= 5 ? 'text-accent-gold' : team.p_champion >= 1 ? 'text-accent-amber' : 'text-text-secondary/50'}`}>
                  {team.p_champion > 0 ? `${team.p_champion}%` : '—'}
                </span>
                <span className="text-xs text-center text-text-secondary">
                  {team.p_finalist > 0 ? `${team.p_finalist}%` : '—'}
                </span>
                <span className="text-xs text-center text-text-secondary">
                  {team.p_top4 > 0 ? `${team.p_top4}%` : '—'}
                </span>
                <span className="text-xs text-center text-text-secondary">
                  {team.p_top8 > 0 ? `${team.p_top8}%` : '—'}
                </span>
                <span className={`text-xs text-center font-medium ${team.p_group_advance >= 70 ? 'text-success' : team.p_group_advance >= 40 ? 'text-accent-amber' : 'text-danger'}`}>
                  {team.p_group_advance}%
                </span>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>

      {/* Footer note */}
      {generatedAt && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="text-[10px] text-text-secondary/40 text-center"
        >
          Generado {new Date(generatedAt).toLocaleString('es-CO')} · {simCount.toLocaleString()} simulaciones · Caché 1 hora
        </motion.p>
      )}
    </div>
  );
}
