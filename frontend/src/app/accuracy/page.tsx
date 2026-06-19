'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, CheckCircle2, XCircle, Target, AlertTriangle, RefreshCw, TrendingUp } from 'lucide-react';
import { api } from '@/lib/api';
import FlagImg from '@/components/ui/FlagImg';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AccMatch {
  match_id: number;
  match_date: string;
  stage: string;
  stage_label: string;
  group?: string | null;
  home: string;
  away: string;
  home_name: string;
  away_name: string;
  home_flag_url: string;
  away_flag_url: string;
  actual_home: number;
  actual_away: number;
  predicted_home: number;
  predicted_away: number;
  actual_outcome: 'home' | 'draw' | 'away';
  pred_outcome: 'home' | 'draw' | 'away';
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  confidence: number;
  prob_actual_outcome: number;
  outcome_hit: boolean;
  exact_hit: boolean;
  points: number;
}

interface AccData {
  evaluated: number;
  outcome_correct: number;
  outcome_accuracy_pct: number;
  exact_correct: number;
  exact_accuracy_pct: number;
  total_points: number;
  max_points: number;
  avg_points: number;
  avg_confidence: number;
  brier_score: number | null;
  stage_breakdown: { label: string; total: number; correct: number; accuracy: number | null }[];
  confidence_breakdown: { label: string; total: number; correct: number; accuracy: number | null }[];
  matches: AccMatch[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtDate(s: string) {
  const d = new Date(s.replace(' ', 'T'));
  if (isNaN(d.getTime())) return '';
  return d.toLocaleDateString('es', { day: '2-digit', month: 'short' });
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

function PointsBadge({ pts }: { pts: number }) {
  const cfg = pts === 3
    ? { bg: 'rgba(34,197,94,0.12)', bd: 'rgba(34,197,94,0.3)', tx: 'text-success' }
    : pts === 1
    ? { bg: 'rgba(245,158,11,0.12)', bd: 'rgba(245,158,11,0.3)', tx: 'text-accent-amber' }
    : { bg: 'rgba(239,68,68,0.10)', bd: 'rgba(239,68,68,0.25)', tx: 'text-danger' };
  return (
    <span className={`inline-block px-2 py-0.5 rounded-md text-[11px] font-bold tabular-nums ${cfg.tx}`}
      style={{ background: cfg.bg, border: `1px solid ${cfg.bd}` }}>
      {pts} pt{pts === 1 ? '' : 's'}
    </span>
  );
}

function MatchRow({ m, delay }: { m: AccMatch; delay: number }) {
  return (
    <motion.tr
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay, ease: 'easeOut' as const }}
      className={`border-b transition-colors ${
        m.outcome_hit
          ? 'border-success/10 hover:bg-success/[0.03]'
          : 'border-danger/10 hover:bg-danger/[0.03]'
      }`}
    >
      {/* Date / stage */}
      <td className="py-2.5 pl-4 pr-3 whitespace-nowrap">
        <span className="text-[11px] text-text-secondary font-medium">{fmtDate(m.match_date)}</span>
        <span className="block text-[9px] text-text-muted">{m.group ? `Gr. ${m.group}` : m.stage_label}</span>
      </td>

      {/* Teams */}
      <td className="py-2.5 pr-4">
        <div className="flex items-center gap-1.5">
          <FlagImg teamCode={m.home} name={m.home_name} url={m.home_flag_url} size="sm" />
          <span className="text-xs font-semibold text-text-primary">{m.home}</span>
          <span className="text-text-muted text-[10px] mx-1">vs</span>
          <FlagImg teamCode={m.away} name={m.away_name} url={m.away_flag_url} size="sm" />
          <span className="text-xs font-semibold text-text-primary">{m.away}</span>
        </div>
      </td>

      {/* Real score */}
      <td className="py-2.5 pr-4 text-center">
        <span className="text-sm font-black text-text-primary stat-value">{m.actual_home}–{m.actual_away}</span>
      </td>

      {/* Predicted score */}
      <td className="py-2.5 pr-4 text-center">
        <span className={`text-sm font-bold stat-value ${m.exact_hit ? 'text-success' : 'text-text-secondary'}`}>
          {m.predicted_home}–{m.predicted_away}
        </span>
      </td>

      {/* Prob bar */}
      <td className="py-2.5 pr-4 min-w-[100px]">
        <div className="space-y-1">
          <ProbBar hw={m.home_win_prob} dw={m.draw_prob} aw={m.away_win_prob} />
          <div className="flex justify-between text-[9px] text-text-muted">
            <span>{m.home_win_prob}%</span>
            <span>{m.draw_prob}%</span>
            <span>{m.away_win_prob}%</span>
          </div>
        </div>
      </td>

      {/* Confidence */}
      <td className="py-2.5 pr-4 text-center">
        <span className={`text-[11px] font-semibold tabular-nums ${
          m.confidence >= 60 ? 'text-info' : 'text-text-secondary'
        }`}>{m.confidence}%</span>
      </td>

      {/* Hit */}
      <td className="py-2.5 pr-4 text-center">
        {m.outcome_hit
          ? <CheckCircle2 className="w-4 h-4 text-success mx-auto" />
          : <XCircle className="w-4 h-4 text-danger mx-auto" />}
      </td>

      {/* Points */}
      <td className="py-2.5 pr-4 text-center">
        <PointsBadge pts={m.points} />
      </td>
    </motion.tr>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function AccuracyPage() {
  const [data, setData] = useState<AccData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'hit' | 'miss'>('all');

  const load = async (refresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAIAccuracy(refresh);
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = (data?.matches ?? []).filter(m =>
    filter === 'all' ? true : filter === 'hit' ? m.outcome_hit : !m.outcome_hit
  );

  return (
    <div className="max-w-[1280px] mx-auto space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: 'easeOut' as const }}
        className="relative overflow-hidden rounded-3xl p-6 sm:p-8"
        style={{
          background: 'linear-gradient(135deg, rgba(34,197,94,0.12) 0%, rgba(15,15,26,0.95) 50%, rgba(224,180,74,0.08) 100%)',
          border: '1px solid rgba(34,197,94,0.2)',
          boxShadow: '0 8px 40px rgba(0,0,0,0.3)',
        }}
      >
        <div className="absolute top-0 left-[15%] right-[15%] h-px"
          style={{ background: 'linear-gradient(90deg, transparent, rgba(34,197,94,0.5), transparent)' }} />
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-5 h-5 text-success" />
              <span className="text-xs font-semibold text-success uppercase tracking-widest">Mundial 2026 · En Vivo</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-text-primary leading-tight" style={{ letterSpacing: '-0.02em' }}>
              Efectividad de la IA
            </h1>
            <p className="text-text-secondary text-sm mt-1">
              Predicciones pasadas frente a resultados reales — se actualiza solo cada día con los marcadores
            </p>
          </div>
          <button
            onClick={() => load(true)}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-accent-gold border border-accent-gold/20 hover:border-accent-gold/40 hover:bg-accent-gold/5 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Actualizando…' : 'Actualizar'}
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

      {data && data.evaluated === 0 && (
        <div className="rounded-2xl p-8 text-center border border-white/[0.06]" style={{ background: 'rgba(15,15,26,0.9)' }}>
          <Target className="w-8 h-8 text-text-muted mx-auto mb-3" />
          <p className="text-text-secondary text-sm">Aún no hay partidos jugados con predicción para evaluar.</p>
        </div>
      )}

      {data && data.evaluated > 0 && (
        <>
          {/* Metric cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <MetricCard
              value={`${data.outcome_accuracy_pct}%`}
              label="Acierto de Resultado"
              sub={`${data.outcome_correct} de ${data.evaluated} partidos`}
              color="green"
            />
            <MetricCard
              value={`${data.exact_accuracy_pct}%`}
              label="Marcador Exacto"
              sub={`${data.exact_correct} marcadores clavados`}
              color="gold"
            />
            <MetricCard
              value={data.total_points}
              label="Puntos Polla"
              sub={`de ${data.max_points} · ${data.avg_points}/partido`}
              color="amber"
            />
            <MetricCard
              value={`${data.avg_confidence}%`}
              label="Confianza Media"
              sub={data.brier_score !== null ? `Brier ${data.brier_score}` : undefined}
              color="blue"
            />
          </div>

          {/* Confidence calibration */}
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
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-4 h-4 text-info" />
              <h2 className="section-title">Calibración por Confianza</h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {data.confidence_breakdown.map((c, i) => (
                <div key={i} className="text-center p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
                  <p className="text-[10px] text-text-muted uppercase tracking-wider mb-1">Conf. {c.label}</p>
                  <p className={`text-xl font-black stat-value ${
                    c.accuracy === null ? 'text-text-muted' :
                    c.accuracy >= 60 ? 'text-success' :
                    c.accuracy >= 40 ? 'text-accent-amber' : 'text-danger'
                  }`}>
                    {c.accuracy !== null ? `${c.accuracy}%` : '—'}
                  </p>
                  <p className="text-[9px] text-text-muted mt-0.5">{c.correct}/{c.total} aciertos</p>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-text-muted mt-3">
              Una IA bien calibrada acierta más cuanto mayor es su confianza. Cada celda muestra el % real de aciertos en ese rango.
            </p>
          </motion.div>

          {/* Filter tabs */}
          <div className="flex gap-2 flex-wrap">
            {[
              { key: 'all', label: `Todos (${data.matches.length})` },
              { key: 'hit', label: `Aciertos (${data.outcome_correct})` },
              { key: 'miss', label: `Fallos (${data.evaluated - data.outcome_correct})` },
            ].map(opt => (
              <button
                key={opt.key}
                onClick={() => setFilter(opt.key as 'all' | 'hit' | 'miss')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 border ${
                  filter === opt.key
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
              <h2 className="section-title">Historial de Predicciones</h2>
              <span className="text-[11px] text-text-muted">{filtered.length} partidos · más recientes primero</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    {['Fecha', 'Equipos', 'Real', 'Pred.', 'Prob. L / E / V', 'Conf.', '✓', 'Puntos'].map(h => (
                      <th key={h} className="py-2.5 pl-4 pr-2 text-[10px] font-semibold text-text-muted uppercase tracking-wider whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((m, i) => (
                    <MatchRow key={m.match_id} m={m} delay={Math.min(i * 0.01, 0.3)} />
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Legend */}
          <div className="flex flex-wrap gap-4 text-[11px] text-text-muted pb-4">
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-success" />Resultado acertado</span>
            <span className="flex items-center gap-1.5"><XCircle className="w-3.5 h-3.5 text-danger" />Resultado fallado</span>
            <span><span className="text-success font-semibold">3 pts</span> marcador exacto · <span className="text-accent-amber font-semibold">1 pt</span> resultado · <span className="text-danger font-semibold">0</span> fallo</span>
          </div>
        </>
      )}
    </div>
  );
}
