'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FlaskConical, CheckCircle2, XCircle, Minus, TrendingUp, AlertTriangle, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';
import FlagImg from '@/components/ui/FlagImg';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MatchResult {
  idx: number;
  stage: string;
  stage_label: string;
  group?: string;
  home: string;
  away: string;
  actual_hg: number;
  actual_ag: number;
  actual_outcome: 'home' | 'draw' | 'away';
  went_to_pens: boolean;
  status: 'ok' | 'skipped' | 'error';
  skipped_reason?: string;
  predicted_hg?: number;
  predicted_ag?: number;
  pred_outcome?: 'home' | 'draw' | 'away';
  home_win_prob?: number;
  draw_prob?: number;
  away_win_prob?: number;
  confidence?: number;
  prob_actual_outcome?: number;
  hit?: boolean;
  home_elo?: number;
  away_elo?: number;
}

interface BacktestData {
  total_matches: number;
  processed: number;
  skipped: number;
  skipped_teams: string[];
  correct_outcomes: number;
  accuracy_pct: number;
  avg_prob_actual_outcome: number;
  stage_breakdown: { label: string; total: number; correct: number; skipped: number; accuracy: number | null }[];
  matches: MatchResult[];
  top_upsets_missed: MatchResult[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STAGE_ORDER = ['group', 'r16', 'qf', 'sf', '3rd', 'final'];

function outcomeLabel(o: string) {
  if (o === 'home') return 'Local';
  if (o === 'away') return 'Visitante';
  return 'Empate';
}

function outcomeColor(hit: boolean | undefined, status: string) {
  if (status !== 'ok') return 'text-text-muted';
  return hit ? 'text-success' : 'text-danger';
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MetricCard({ value, label, sub, color = 'gold' }: { value: React.ReactNode; label: string; sub?: string; color?: string }) {
  const colors: Record<string, string> = {
    gold: 'border-accent-gold/20 text-accent-gold',
    green: 'border-success/20 text-success',
    blue: 'border-info/20 text-info',
    amber: 'border-accent-amber/20 text-accent-amber',
  };
  return (
    <div
      className={`rounded-2xl p-5 border ${colors[color] ?? colors.gold}`}
      style={{ background: 'linear-gradient(135deg, rgba(15,15,26,0.92) 0%, rgba(18,16,32,0.88) 100%)' }}
    >
      <p className="text-3xl font-black stat-value" style={{ letterSpacing: '-0.03em' }}>{value}</p>
      <p className="text-xs text-text-secondary font-medium uppercase tracking-wider mt-1">{label}</p>
      {sub && <p className="text-[10px] text-text-muted mt-0.5">{sub}</p>}
    </div>
  );
}

function ProbBar({ hw, dw, aw }: { hw: number; dw: number; aw: number }) {
  return (
    <div className="flex h-1.5 rounded-full overflow-hidden w-full gap-px">
      <div className="bg-info/70 rounded-l-full" style={{ width: `${hw}%` }} />
      <div className="bg-text-muted/40" style={{ width: `${dw}%` }} />
      <div className="bg-danger/70 rounded-r-full" style={{ width: `${aw}%` }} />
    </div>
  );
}

function MatchRow({ m, delay }: { m: MatchResult; delay: number }) {
  const isOk = m.status === 'ok';
  const hit = isOk && m.hit;

  return (
    <motion.tr
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay, ease: 'easeOut' as const }}
      className={`border-b transition-colors ${
        hit === true
          ? 'border-success/10 hover:bg-success/[0.03]'
          : hit === false
          ? 'border-danger/10 hover:bg-danger/[0.03]'
          : 'border-white/[0.04] hover:bg-white/[0.015]'
      }`}
    >
      {/* # */}
      <td className="py-2.5 pl-4 pr-2 text-[10px] text-text-muted tabular-nums w-8">{m.idx}</td>

      {/* Stage */}
      <td className="py-2.5 pr-3 text-[10px] text-text-muted whitespace-nowrap">
        <span className="px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06]">
          {m.group ? `Gr. ${m.group}` : m.stage_label}
        </span>
      </td>

      {/* Teams */}
      <td className="py-2.5 pr-4">
        <div className="flex items-center gap-1.5">
          <FlagImg teamCode={m.home} name={m.home} size="sm" />
          <span className="text-xs font-semibold text-text-primary">{m.home}</span>
          <span className="text-text-muted text-[10px] mx-1">vs</span>
          <FlagImg teamCode={m.away} name={m.away} size="sm" />
          <span className="text-xs font-semibold text-text-primary">{m.away}</span>
        </div>
      </td>

      {/* Actual score */}
      <td className="py-2.5 pr-4 text-center">
        <span className="text-sm font-black text-text-primary stat-value">
          {m.actual_hg}–{m.actual_ag}
        </span>
        {m.went_to_pens && (
          <span className="block text-[9px] text-text-muted">pen.</span>
        )}
      </td>

      {/* Predicted score */}
      <td className="py-2.5 pr-4 text-center">
        {isOk ? (
          <span className="text-sm font-bold text-text-secondary stat-value">
            {m.predicted_hg}–{m.predicted_ag}
          </span>
        ) : (
          <span className="text-[10px] text-text-muted">—</span>
        )}
      </td>

      {/* Prob bar */}
      <td className="py-2.5 pr-4 min-w-[100px]">
        {isOk && m.home_win_prob !== undefined ? (
          <div className="space-y-1">
            <ProbBar hw={m.home_win_prob} dw={m.draw_prob!} aw={m.away_win_prob!} />
            <div className="flex justify-between text-[9px] text-text-muted">
              <span>{m.home_win_prob}%</span>
              <span>{m.draw_prob}%</span>
              <span>{m.away_win_prob}%</span>
            </div>
          </div>
        ) : (
          <span className="text-[10px] text-text-muted">
            {m.skipped_reason ? 'Sin datos' : '—'}
          </span>
        )}
      </td>

      {/* Predicted outcome */}
      <td className="py-2.5 pr-4 text-center">
        {isOk ? (
          <span className="text-[10px] font-medium text-text-secondary">
            {outcomeLabel(m.pred_outcome!)}
          </span>
        ) : (
          <span className="text-[10px] text-text-muted">—</span>
        )}
      </td>

      {/* Actual outcome */}
      <td className="py-2.5 pr-4 text-center">
        <span className="text-[10px] font-medium text-text-secondary">
          {outcomeLabel(m.actual_outcome)}
        </span>
      </td>

      {/* Hit */}
      <td className="py-2.5 pr-4 text-center">
        {isOk ? (
          hit ? (
            <CheckCircle2 className="w-4 h-4 text-success mx-auto" />
          ) : (
            <XCircle className="w-4 h-4 text-danger mx-auto" />
          )
        ) : (
          <Minus className="w-3.5 h-3.5 text-text-muted mx-auto" />
        )}
      </td>

      {/* Prob of actual */}
      <td className="py-2.5 pr-4 text-center">
        {isOk && m.prob_actual_outcome !== undefined ? (
          <span className={`text-[11px] font-semibold tabular-nums ${
            m.prob_actual_outcome >= 50 ? 'text-success' :
            m.prob_actual_outcome >= 35 ? 'text-accent-amber' : 'text-danger'
          }`}>
            {m.prob_actual_outcome}%
          </span>
        ) : (
          <span className="text-[10px] text-text-muted">—</span>
        )}
      </td>
    </motion.tr>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function BacktestPage() {
  const [data, setData] = useState<BacktestData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<string>('all');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getQatar2022Backtest();
      setData(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filteredMatches = data?.matches.filter(m =>
    activeStage === 'all' || m.stage === activeStage
  ) ?? [];

  const stageOptions = [
    { key: 'all', label: 'Todos' },
    { key: 'group', label: 'Grupos' },
    { key: 'r16', label: 'Octavos' },
    { key: 'qf', label: 'Cuartos' },
    { key: 'sf', label: 'Semis' },
    { key: 'final', label: 'Final' },
  ];

  return (
    <div className="max-w-[1280px] mx-auto space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: 'easeOut' as const }}
        className="relative overflow-hidden rounded-3xl p-6 sm:p-8"
        style={{
          background: 'linear-gradient(135deg, rgba(139,92,246,0.12) 0%, rgba(15,15,26,0.95) 50%, rgba(224,180,74,0.08) 100%)',
          border: '1px solid rgba(139,92,246,0.2)',
          boxShadow: '0 8px 40px rgba(0,0,0,0.3)',
        }}
      >
        <div className="absolute top-0 left-[15%] right-[15%] h-px"
          style={{ background: 'linear-gradient(90deg, transparent, rgba(139,92,246,0.5), transparent)' }} />
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <FlaskConical className="w-5 h-5 text-accent-purple" />
              <span className="text-xs font-semibold text-accent-purple uppercase tracking-widest">Validación Retroactiva</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-text-primary leading-tight" style={{ letterSpacing: '-0.02em' }}>
              Backtest · Qatar 2022
            </h1>
            <p className="text-text-secondary text-sm mt-1">
              El modelo Poisson + ELO analiza los 64 partidos del Mundial 2022 con datos actuales
            </p>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-accent-gold border border-accent-gold/20 hover:border-accent-gold/40 hover:bg-accent-gold/5 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Calculando…' : 'Recalcular'}
          </button>
        </div>
      </motion.div>

      {/* Error */}
      {error && (
        <div className="rounded-2xl p-5 border border-danger/20 bg-danger/5 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-danger flex-shrink-0" />
          <p className="text-sm text-danger">{error}</p>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && !data && (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="rounded-2xl h-20 animate-pulse" style={{ background: 'rgba(255,255,255,0.03)' }} />
          ))}
        </div>
      )}

      {data && (
        <>
          {/* Metric cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <MetricCard
              value={`${data.accuracy_pct}%`}
              label="Precisión de Resultados"
              sub={`${data.correct_outcomes} de ${data.processed} partidos`}
              color="green"
            />
            <MetricCard
              value={`${data.avg_prob_actual_outcome}%`}
              label="Prob. Media (resultado real)"
              sub="Calibración del modelo"
              color="blue"
            />
            <MetricCard
              value={data.processed}
              label="Partidos Analizados"
              sub={`${data.skipped} omitidos sin datos`}
              color="gold"
            />
            <MetricCard
              value={data.correct_outcomes}
              label="Resultados Correctos"
              sub={`de ${data.processed} predichos`}
              color="amber"
            />
          </div>

          {/* Stage breakdown */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.15, ease: 'easeOut' as const }}
            className="rounded-2xl p-5"
            style={{
              background: 'linear-gradient(135deg, rgba(15,15,26,0.92) 0%, rgba(18,16,32,0.88) 100%)',
              border: '1px solid rgba(255,255,255,0.06)',
            }}
          >
            <h2 className="section-title mb-4">Precisión por Fase</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {data.stage_breakdown.map((s, i) => (
                <div key={i} className="text-center p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
                  <p className="text-[10px] text-text-muted uppercase tracking-wider mb-1">{s.label}</p>
                  <p className={`text-xl font-black stat-value ${
                    s.accuracy === null ? 'text-text-muted' :
                    s.accuracy >= 60 ? 'text-success' :
                    s.accuracy >= 40 ? 'text-accent-amber' : 'text-danger'
                  }`}>
                    {s.accuracy !== null ? `${s.accuracy}%` : '—'}
                  </p>
                  <p className="text-[9px] text-text-muted mt-0.5">{s.correct}/{s.total}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Notable upsets missed */}
          {data.top_upsets_missed.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2, ease: 'easeOut' as const }}
              className="rounded-2xl p-5"
              style={{
                background: 'linear-gradient(135deg, rgba(239,68,68,0.06) 0%, rgba(15,15,26,0.92) 100%)',
                border: '1px solid rgba(239,68,68,0.12)',
              }}
            >
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="w-4 h-4 text-danger" />
                <h2 className="section-title">Mayores Sorpresas no Previstas</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {data.top_upsets_missed.map((m, i) => (
                  <div key={i} className="p-3 rounded-xl" style={{ background: 'rgba(239,68,68,0.04)', border: '1px solid rgba(239,68,68,0.1)' }}>
                    <div className="flex items-center gap-2 mb-1">
                      <FlagImg teamCode={m.home} name={m.home} size="sm" />
                      <span className="text-xs font-bold text-text-primary">{m.home}</span>
                      <span className="text-text-muted text-[10px]">vs</span>
                      <FlagImg teamCode={m.away} name={m.away} size="sm" />
                      <span className="text-xs font-bold text-text-primary">{m.away}</span>
                    </div>
                    <p className="text-[10px] text-text-muted">
                      Real: <span className="text-text-secondary font-semibold">{m.actual_hg}–{m.actual_ag}</span>
                      {' · '}Pred: <span className="text-text-secondary font-semibold">{m.predicted_hg}–{m.predicted_ag}</span>
                    </p>
                    <p className="text-[10px] mt-0.5">
                      <span className="text-danger">Predijo {outcomeLabel(m.pred_outcome!)} ({
                        m.pred_outcome === 'home' ? m.home_win_prob : m.pred_outcome === 'away' ? m.away_win_prob : m.draw_prob
                      }%)</span>
                      {' → '}
                      <span className="text-text-secondary">Ganó {outcomeLabel(m.actual_outcome)}</span>
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Skipped teams notice */}
          {data.skipped_teams.length > 0 && (
            <div className="rounded-xl px-4 py-3 flex items-start gap-2" style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.15)' }}>
              <AlertTriangle className="w-3.5 h-3.5 text-accent-amber mt-0.5 flex-shrink-0" />
              <p className="text-[11px] text-text-muted">
                <span className="text-accent-amber font-semibold">{data.skipped} partidos omitidos</span>
                {' — '}equipos no encontrados en la base de datos 2026:{' '}
                <span className="text-text-secondary">{data.skipped_teams.join(', ')}</span>
              </p>
            </div>
          )}

          {/* Stage filter tabs */}
          <div className="flex gap-2 flex-wrap">
            {stageOptions.map(opt => (
              <button
                key={opt.key}
                onClick={() => setActiveStage(opt.key)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 border ${
                  activeStage === opt.key
                    ? 'bg-accent-gold/10 text-accent-gold border-accent-gold/25'
                    : 'text-text-secondary border-white/[0.06] hover:border-white/[0.12] hover:text-text-primary'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* Match table */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.25, ease: 'easeOut' as const }}
            className="rounded-2xl overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, rgba(15,15,26,0.92) 0%, rgba(18,16,32,0.88) 100%)',
              border: '1px solid rgba(255,255,255,0.06)',
            }}
          >
            <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <h2 className="section-title">Resultados Partido a Partido</h2>
              <span className="text-[11px] text-text-muted">{filteredMatches.length} partidos</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    {['#', 'Fase', 'Equipos', 'Real', 'Pred.', 'Prob. H / E / A', 'Pred. resultado', 'Real resultado', '✓', 'P(real)'].map(h => (
                      <th key={h} className="py-2.5 pl-4 pr-2 text-[10px] font-semibold text-text-muted uppercase tracking-wider whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredMatches.map((m, i) => (
                    <MatchRow key={m.idx} m={m} delay={Math.min(i * 0.01, 0.3)} />
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Legend */}
          <div className="flex flex-wrap gap-4 text-[11px] text-text-muted pb-4">
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-success" />Resultado correcto</span>
            <span className="flex items-center gap-1.5"><XCircle className="w-3.5 h-3.5 text-danger" />Resultado incorrecto</span>
            <span className="flex items-center gap-1.5"><Minus className="w-3.5 h-3.5 text-text-muted" />Sin datos (equipo no en DB 2026)</span>
            <span>P(real) = probabilidad asignada al resultado que ocurrió</span>
          </div>
        </>
      )}
    </div>
  );
}
