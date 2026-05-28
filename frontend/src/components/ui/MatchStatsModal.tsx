'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, TrendingUp, Shield, Zap, Activity, Target, Users } from 'lucide-react';
import FlagImg from '@/components/ui/FlagImg';
import { api } from '@/lib/api';
import type { Match } from '@/types';

interface MatchStatsModalProps {
  match: Match | null;
  onClose: () => void;
}

function Bar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="w-full h-1.5 rounded-full bg-bg-tertiary/60">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className={`h-full rounded-full ${color}`}
      />
    </div>
  );
}

function ProbBar({ homeProb, drawProb, awayProb }: { homeProb: number; drawProb: number; awayProb: number }) {
  const hp = Math.round(homeProb * 100);
  const dp = Math.round(drawProb * 100);
  const ap = Math.round(awayProb * 100);
  return (
    <div className="w-full">
      <div className="flex rounded-full overflow-hidden h-3">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${hp}%` }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
          className="bg-success h-full"
        />
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${dp}%` }}
          transition={{ duration: 0.7, ease: 'easeOut', delay: 0.1 }}
          className="bg-accent-amber h-full"
        />
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${ap}%` }}
          transition={{ duration: 0.7, ease: 'easeOut', delay: 0.2 }}
          className="bg-danger h-full"
        />
      </div>
      <div className="flex justify-between mt-1.5 text-xs">
        <span className="text-success font-semibold">{hp}%</span>
        <span className="text-accent-amber font-semibold">{dp}%</span>
        <span className="text-danger font-semibold">{ap}%</span>
      </div>
      <div className="flex justify-between text-[10px] text-text-secondary/60">
        <span>Local</span>
        <span>Empate</span>
        <span>Visitante</span>
      </div>
    </div>
  );
}

function StatRow({
  label,
  homeVal,
  awayVal,
  format = (v: number) => v.toString(),
  higherIsBetter = true,
  icon: Icon,
}: {
  label: string;
  homeVal: number;
  awayVal: number;
  format?: (v: number) => string;
  higherIsBetter?: boolean;
  icon: React.ElementType;
}) {
  const max = Math.max(homeVal, awayVal, 0.01);
  const homeWins = higherIsBetter ? homeVal >= awayVal : homeVal <= awayVal;
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
      {/* Home value */}
      <div className="text-right">
        <span className={`text-sm font-bold ${homeWins ? 'text-accent-gold' : 'text-text-secondary'}`}>
          {format(homeVal)}
        </span>
        <Bar value={homeWins ? homeVal : awayVal - (awayVal - homeVal)} max={max} color={homeWins ? 'bg-accent-gold' : 'bg-text-secondary/30'} />
      </div>
      {/* Label */}
      <div className="flex flex-col items-center gap-0.5 min-w-[90px]">
        <Icon className="w-3.5 h-3.5 text-text-secondary/60" />
        <span className="text-[10px] text-text-secondary/70 text-center leading-tight">{label}</span>
      </div>
      {/* Away value */}
      <div className="text-left">
        <span className={`text-sm font-bold ${!homeWins ? 'text-accent-gold' : 'text-text-secondary'}`}>
          {format(awayVal)}
        </span>
        <Bar value={!homeWins ? awayVal : homeVal - (homeVal - awayVal)} max={max} color={!homeWins ? 'bg-accent-gold' : 'bg-text-secondary/30'} />
      </div>
    </div>
  );
}

export default function MatchStatsModal({ match, onClose }: MatchStatsModalProps) {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (id: number) => {
    setLoading(true);
    setAnalysis(null);
    try {
      const data = await api.getMatchAnalysis(id);
      setAnalysis(data);
    } catch {
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (match?.id) load(match.id);
  }, [match?.id, load]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  if (!match) return null;

  const sp = analysis?.statistical_prediction;
  const confidence = sp ? Math.round(sp.confidence * 100) : null;
  const confidenceColor =
    confidence === null ? 'text-text-secondary'
    : confidence >= 80 ? 'text-success'
    : confidence >= 65 ? 'text-accent-gold'
    : 'text-accent-amber';

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.25 }}
          onClick={e => e.stopPropagation()}
          className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-bg-secondary border border-accent-gold/15 shadow-2xl"
        >
          {/* Header */}
          <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-4 bg-bg-secondary/95 backdrop-blur-sm border-b border-accent-gold/10">
            <span className="text-xs font-semibold text-accent-gold/80 uppercase tracking-wider">
              {match.group ? `Grupo ${match.group} · ` : ''}{match.stage === 'group' ? 'Fase de Grupos' : 'Eliminatoria'}
            </span>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-bg-tertiary/60 transition-colors text-text-secondary hover:text-text-primary"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="p-5 space-y-5">
            {/* Teams header */}
            <div className="flex items-center justify-between gap-3">
              <div className="flex-1 flex flex-col items-center gap-2">
                <FlagImg url={(match as any).home_flag_url} emoji={match.home_flag} teamCode={match.home_team} name={match.home_team_name} size="lg" />
                <p className="text-sm font-bold text-text-primary text-center">{match.home_team_name}</p>
                <span className="text-[10px] text-text-secondary/60 uppercase">{match.home_team}</span>
              </div>

              <div className="flex flex-col items-center gap-1">
                {sp ? (
                  <>
                    <div className="flex items-center gap-2">
                      <span className="text-3xl font-bold text-text-primary">{sp.predicted_home_score}</span>
                      <span className="text-text-secondary">-</span>
                      <span className="text-3xl font-bold text-text-primary">{sp.predicted_away_score}</span>
                    </div>
                    <span className="text-[10px] text-text-secondary/60">Pronóstico</span>
                  </>
                ) : (
                  <span className="text-xl font-bold text-accent-gold">vs</span>
                )}
                <div className="text-[10px] text-text-secondary/50 text-center mt-1">
                  {match.date} · {match.time}
                </div>
              </div>

              <div className="flex-1 flex flex-col items-center gap-2">
                <FlagImg url={(match as any).away_flag_url} emoji={match.away_flag} teamCode={match.away_team} name={match.away_team_name} size="lg" />
                <p className="text-sm font-bold text-text-primary text-center">{match.away_team_name}</p>
                <span className="text-[10px] text-text-secondary/60 uppercase">{match.away_team}</span>
              </div>
            </div>

            {/* Loading */}
            {loading && (
              <div className="flex items-center justify-center py-8 gap-3">
                <div className="w-5 h-5 border-2 border-accent-gold/30 border-t-accent-gold rounded-full animate-spin" />
                <span className="text-sm text-text-secondary">Calculando estadísticas...</span>
              </div>
            )}

            {/* Stats */}
            {sp && !loading && (
              <>
                {/* Confidence */}
                <div className="flex items-center justify-center gap-2 py-2 px-4 rounded-xl bg-bg-tertiary/40 border border-accent-gold/8">
                  <Activity className="w-4 h-4 text-text-secondary/60" />
                  <span className="text-xs text-text-secondary">Confianza del modelo:</span>
                  <span className={`text-sm font-bold ${confidenceColor}`}>{confidence}%</span>
                </div>

                {/* Probability bar */}
                <div>
                  <p className="text-xs text-text-secondary mb-2">Probabilidades</p>
                  <ProbBar
                    homeProb={sp.home_win_prob}
                    drawProb={sp.draw_prob}
                    awayProb={sp.away_win_prob}
                  />
                </div>

                {/* Stat rows */}
                <div className="space-y-4">
                  <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Comparativa</p>

                  <StatRow
                    label="ELO Rating"
                    homeVal={sp.home_elo}
                    awayVal={sp.away_elo}
                    format={v => v.toFixed(0)}
                    icon={TrendingUp}
                  />
                  <StatRow
                    label="Fuerza Global"
                    homeVal={sp.home_strength}
                    awayVal={sp.away_strength}
                    format={v => v.toFixed(1)}
                    icon={Shield}
                  />
                  <StatRow
                    label="xG Ataque"
                    homeVal={sp.home_xg_for}
                    awayVal={sp.away_xg_for}
                    format={v => v.toFixed(2)}
                    icon={Target}
                  />
                  <StatRow
                    label="xG Defensa"
                    homeVal={sp.home_xg_against}
                    awayVal={sp.away_xg_against}
                    format={v => v.toFixed(2)}
                    higherIsBetter={false}
                    icon={Shield}
                  />
                  <StatRow
                    label="Lambda (goles esp.)"
                    homeVal={sp.poisson_home_lambda}
                    awayVal={sp.poisson_away_lambda}
                    format={v => v.toFixed(2)}
                    icon={Zap}
                  />
                </div>

                {/* Modifiers */}
                <div className="rounded-xl border border-accent-gold/8 bg-bg-tertiary/30 p-4 space-y-2">
                  <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Factores del modelo</p>
                  {[
                    { label: 'Forma reciente', home: sp.home_form_mod, away: sp.away_form_mod },
                    { label: 'Historial H2H', home: sp.home_h2h_mod, away: sp.away_h2h_mod },
                    { label: 'Bajas / lesiones', home: sp.home_absence_mod, away: sp.away_absence_mod },
                    { label: 'Clima / altitud', home: sp.home_climate_mod, away: sp.away_climate_mod },
                  ].map(({ label, home, away }) => (
                    <div key={label} className="flex items-center justify-between text-xs">
                      <span className={`w-16 text-right font-mono ${home > 0 ? 'text-success' : home < 0 ? 'text-danger' : 'text-text-secondary/50'}`}>
                        {home > 0 ? '+' : ''}{(home * 100).toFixed(1)}%
                      </span>
                      <span className="text-text-secondary/60 flex-1 text-center">{label}</span>
                      <span className={`w-16 text-left font-mono ${away > 0 ? 'text-success' : away < 0 ? 'text-danger' : 'text-text-secondary/50'}`}>
                        {away > 0 ? '+' : ''}{(away * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                  <div className="flex justify-between text-[10px] text-text-secondary/40 pt-1 border-t border-accent-gold/8 mt-2">
                    <span>{match.home_team_name}</span>
                    <span>{match.away_team_name}</span>
                  </div>
                </div>

                {/* Venue */}
                <div className="text-center text-xs text-text-secondary/50">
                  {match.venue}, {match.city}
                </div>
              </>
            )}

            {!sp && !loading && (
              <div className="text-center py-8 text-text-secondary text-sm">
                No se pudieron cargar las estadísticas
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
