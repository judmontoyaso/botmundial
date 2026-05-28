'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Zap, Shield, TrendingUp, Star, Award,
  Plus, Trash2, AlertCircle,
} from 'lucide-react';
import { api } from '@/lib/api';
import FlagImg from '@/components/ui/FlagImg';
import LoadingBall from '@/components/ui/LoadingBall';

interface TeamAbsence {
  id: number;
  team_code: string;
  player_name: string;
  position?: string;
  importance: number;
  reason: string;
  is_active: boolean;
}

const POSITION_LABELS: Record<string, string> = {
  GK: 'Portero', DEF: 'Defensa', MID: 'Mediocampista', FWD: 'Delantero',
};
const IMPORTANCE_LABELS: Record<number, { label: string; color: string }> = {
  1: { label: 'Rotación', color: 'text-text-secondary' },
  2: { label: 'Titular', color: 'text-accent-amber' },
  3: { label: 'Figura', color: 'text-accent-gold' },
};
const REASON_LABELS: Record<string, string> = {
  injury: 'Lesión', suspension: 'Suspensión', fitness: 'Fitness', other: 'Otro',
};

function StatBox({ label, value, sub, color = 'text-accent-gold' }: {
  label: string; value: string | number; sub?: string; color?: string;
}) {
  return (
    <div className="flex flex-col items-center p-3 rounded-xl bg-bg-tertiary/30 gap-0.5">
      <span className={`text-xl font-bold ${color}`}>{value}</span>
      <span className="text-[10px] text-text-secondary text-center">{label}</span>
      {sub && <span className="text-[9px] text-text-secondary/50">{sub}</span>}
    </div>
  );
}

function FormDots({ form5 }: { form5: number }) {
  return (
    <div className="flex gap-1">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className={`w-2.5 h-2.5 rounded-full ${i < form5 ? 'bg-success' : 'bg-bg-tertiary'}`}
        />
      ))}
    </div>
  );
}

export default function TeamDetailPage() {
  const params = useParams();
  const router = useRouter();
  const code = (params?.code as string ?? '').toUpperCase();

  const [data, setData] = React.useState<any>(null);
  const [absences, setAbsences] = React.useState<TeamAbsence[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [absenceLoading, setAbsenceLoading] = React.useState(false);

  // Add absence form
  const [showForm, setShowForm] = React.useState(false);
  const [formName, setFormName] = React.useState('');
  const [formPos, setFormPos] = React.useState('');
  const [formImportance, setFormImportance] = React.useState(2);
  const [formReason, setFormReason] = React.useState('injury');
  const [submitting, setSubmitting] = React.useState(false);

  async function loadData() {
    try {
      const [analysis, abs] = await Promise.all([
        api.getTeamAnalysis(code),
        api.getTeamAbsences(code).catch(() => ({ data: [] })),
      ]);
      setData(analysis);
      setAbsences(abs.data ?? []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    if (code) loadData();
  }, [code]);

  const handleAddAbsence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) return;
    setSubmitting(true);
    try {
      await api.addTeamAbsence(code, {
        player_name: formName.trim(),
        position: formPos || undefined,
        importance: formImportance,
        reason: formReason,
      });
      const abs = await api.getTeamAbsences(code);
      setAbsences(abs.data ?? []);
      setShowForm(false);
      setFormName(''); setFormPos(''); setFormImportance(2); setFormReason('injury');
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteAbsence = async (id: number) => {
    try {
      await api.deleteAbsence(id);
      setAbsences(prev => prev.filter(a => a.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto h-[60vh] flex flex-col items-center justify-center gap-4">
        <LoadingBall text={`Cargando análisis de ${code}...`} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-4xl mx-auto h-[60vh] flex flex-col items-center justify-center gap-4">
        <AlertCircle className="w-12 h-12 text-danger" />
        <p className="text-text-secondary">Equipo no encontrado.</p>
      </div>
    );
  }

  const team = data.team;
  const stats = team?.stats ?? {};
  const strength = data.strength_score ?? 0;
  const standings = data.predicted_standings ?? [];
  const comparisons = data.comparisons ?? [];
  const teamMatches = data.matches ?? [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors text-sm"
      >
        <ArrowLeft className="w-4 h-4" />
        Volver
      </button>

      {/* Team header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-accent-gold/15 bg-bg-secondary/60 backdrop-blur-xl p-6"
      >
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
          <FlagImg emoji={team?.flag_emoji} teamCode={code} name={team?.name} size="xl" />
          <div className="flex-1 min-w-0">
            <h1 className="text-3xl font-extrabold text-text-primary">{team?.name}</h1>
            <div className="flex flex-wrap items-center gap-3 mt-1">
              <span className="text-text-secondary text-sm">
                Grupo <span className="text-accent-gold font-semibold">{team?.group_letter}</span>
              </span>
              <span className="text-text-secondary text-sm">·</span>
              <span className="text-text-secondary text-sm">{team?.confederation}</span>
              <span className="text-text-secondary text-sm">·</span>
              <span className="text-text-secondary text-sm">FIFA #{team?.fifa_ranking}</span>
            </div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-black gradient-gold-text">{strength}</div>
            <div className="text-[10px] text-text-secondary uppercase tracking-wider">Strength</div>
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mt-5">
          <StatBox label="ELO" value={stats.elo_rating ?? '—'} color="text-accent-gold" />
          <StatBox label="xG Ataque" value={stats.xg_for_avg?.toFixed(2) ?? '—'} color="text-accent-amber" />
          <StatBox label="xG Defensa" value={stats.xg_against_avg?.toFixed(2) ?? '—'} color="text-blue-400" />
          <StatBox label="Portería 0" value={stats.clean_sheets_last_10 ?? 0} sub="últimos 10" color="text-success" />
          <StatBox label="Mundiales" value={stats.world_cup_appearances ?? 0} color="text-text-secondary" />
          <StatBox label="Mejor WC" value={stats.best_finish ?? '—'} color="text-text-secondary" />
        </div>

        {/* Form */}
        <div className="mt-4 flex flex-wrap items-center gap-6">
          <div>
            <p className="text-[10px] text-text-secondary uppercase tracking-wider mb-1.5">Forma últimos 10</p>
            <span className="text-sm font-semibold text-text-primary">
              {stats.wins_last_10}V - {stats.draws_last_10}E - {stats.losses_last_10}D
            </span>
          </div>
          <div>
            <p className="text-[10px] text-text-secondary uppercase tracking-wider mb-1.5">Últimos 5</p>
            <FormDots form5={stats.form_last_5 ?? 0} />
          </div>
          {stats.form_last_5 !== undefined && (
            <div>
              <p className="text-[10px] text-text-secondary uppercase tracking-wider mb-1.5">Racha</p>
              <span className={`text-sm font-semibold ${stats.form_last_5 >= 4 ? 'text-success' : stats.form_last_5 >= 2 ? 'text-accent-amber' : 'text-danger'}`}>
                {stats.form_last_5 >= 4 ? 'Muy buena' : stats.form_last_5 >= 3 ? 'Buena' : stats.form_last_5 >= 2 ? 'Regular' : 'Baja'}
              </span>
            </div>
          )}
        </div>
      </motion.div>

      {/* Group standings + vs rivals */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Predicted standings */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-2xl border border-accent-gold/10 bg-bg-secondary/50 backdrop-blur-xl p-4"
        >
          <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
            <Award className="w-3.5 h-3.5 text-accent-gold" />
            Grupo {team?.group_letter} — Pronóstico
          </h2>
          <div className="space-y-1.5">
            {standings.map((s: any, idx: number) => (
              <div
                key={s.team_code}
                className={`flex items-center gap-3 p-2 rounded-lg ${s.team_code === code ? 'bg-accent-gold/8 border border-accent-gold/15' : ''}`}
              >
                <span className={`text-xs font-bold w-4 text-center ${idx === 0 ? 'text-success' : idx < 2 ? 'text-accent-amber' : 'text-text-secondary/40'}`}>
                  {idx + 1}
                </span>
                <FlagImg teamCode={s.team_code} name={s.team_name} size="sm" />
                <span className={`text-xs flex-1 ${s.team_code === code ? 'font-semibold text-accent-gold' : 'text-text-primary'}`}>
                  {s.team_name}
                </span>
                <span className="text-xs font-bold text-text-primary">{s.points} pts</span>
                <span className={`text-xs ${s.goal_difference > 0 ? 'text-success' : s.goal_difference < 0 ? 'text-danger' : 'text-text-secondary'}`}>
                  {s.goal_difference > 0 ? '+' : ''}{s.goal_difference}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Vs rivals */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.15 }}
          className="rounded-2xl border border-accent-gold/10 bg-bg-secondary/50 backdrop-blur-xl p-4"
        >
          <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
            <TrendingUp className="w-3.5 h-3.5 text-accent-gold" />
            Comparativa vs rivales
          </h2>
          <div className="space-y-3">
            {comparisons.map((cmp: any) => {
              const rival = cmp.team_a.code === code ? cmp.team_b : cmp.team_a;
              const myPct = cmp.team_a.code === code ? cmp.a_win_pct : cmp.b_win_pct;
              const rivPct = 100 - myPct;
              return (
                <div key={rival.code}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1.5">
                      <FlagImg teamCode={rival.code} name={rival.name} size="sm" />
                      <span className="text-xs text-text-secondary">{rival.name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-bold text-accent-gold">{myPct.toFixed(0)}%</span>
                      <span className="text-text-secondary/40">vs</span>
                      <span className="text-text-secondary">{rivPct.toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="h-1.5 bg-bg-tertiary/50 rounded-full overflow-hidden flex">
                    <div className="bg-accent-gold rounded-l-full" style={{ width: `${myPct}%` }} />
                    <div className="bg-bg-tertiary/30 flex-1 rounded-r-full" />
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>

      {/* Upcoming matches */}
      {teamMatches.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl border border-accent-gold/10 bg-bg-secondary/50 backdrop-blur-xl p-4"
        >
          <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
            Partidos de Grupo
          </h2>
          <div className="space-y-2">
            {teamMatches.map((m: any) => {
              const match = m.match ?? m;
              const homeCode = match.home_team_code ?? match.home_team;
              const awayCode = match.away_team_code ?? match.away_team;
              const isHome = homeCode === code;
              return (
                <div key={match.id} className="flex items-center gap-3 p-2.5 rounded-xl bg-bg-tertiary/20">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <FlagImg teamCode={homeCode} name={m.home_team_name ?? homeCode} size="sm" />
                    <span className={`text-xs ${isHome ? 'font-semibold text-accent-gold' : 'text-text-primary'}`}>
                      {m.home_team_name ?? homeCode}
                    </span>
                  </div>
                  <div className="text-center flex-shrink-0">
                    {match.home_score !== null ? (
                      <span className="text-sm font-bold text-text-primary px-2">
                        {match.home_score} - {match.away_score}
                      </span>
                    ) : (
                      <span className="text-[10px] text-text-secondary/50 px-2">vs</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-1 min-w-0 justify-end">
                    <span className={`text-xs ${!isHome ? 'font-semibold text-accent-gold' : 'text-text-primary'}`}>
                      {m.away_team_name ?? awayCode}
                    </span>
                    <FlagImg teamCode={awayCode} name={m.away_team_name ?? awayCode} size="sm" />
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Player absences */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="rounded-2xl border border-accent-gold/10 bg-bg-secondary/50 backdrop-blur-xl p-4"
      >
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 text-danger" />
            Bajas / Lesionados
            {absences.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-danger/15 text-danger text-[9px]">
                {absences.length}
              </span>
            )}
          </h2>
          <button
            onClick={() => setShowForm(v => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent-gold/10 border border-accent-gold/20 text-accent-gold text-xs font-medium hover:bg-accent-gold/15 transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            Agregar
          </button>
        </div>

        {/* Add form */}
        {showForm && (
          <form onSubmit={handleAddAbsence} className="mb-4 p-3 rounded-xl bg-bg-tertiary/30 border border-accent-gold/10 space-y-2">
            <input
              type="text"
              placeholder="Nombre del jugador *"
              value={formName}
              onChange={e => setFormName(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-lg bg-bg-secondary/60 border border-accent-gold/10 text-text-primary text-sm placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-gold/30"
            />
            <div className="grid grid-cols-3 gap-2">
              <select
                value={formPos}
                onChange={e => setFormPos(e.target.value)}
                className="px-2 py-2 rounded-lg bg-bg-secondary/60 border border-accent-gold/10 text-text-primary text-xs focus:outline-none"
              >
                <option value="">Posición</option>
                <option value="GK">Portero</option>
                <option value="DEF">Defensa</option>
                <option value="MID">Mediocampista</option>
                <option value="FWD">Delantero</option>
              </select>
              <select
                value={formImportance}
                onChange={e => setFormImportance(Number(e.target.value))}
                className="px-2 py-2 rounded-lg bg-bg-secondary/60 border border-accent-gold/10 text-text-primary text-xs focus:outline-none"
              >
                <option value={1}>Rotación</option>
                <option value={2}>Titular</option>
                <option value={3}>Figura</option>
              </select>
              <select
                value={formReason}
                onChange={e => setFormReason(e.target.value)}
                className="px-2 py-2 rounded-lg bg-bg-secondary/60 border border-accent-gold/10 text-text-primary text-xs focus:outline-none"
              >
                <option value="injury">Lesión</option>
                <option value="suspension">Suspensión</option>
                <option value="fitness">Fitness</option>
                <option value="other">Otro</option>
              </select>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 py-2 rounded-lg bg-accent-gold/15 border border-accent-gold/20 text-accent-gold text-xs font-semibold hover:bg-accent-gold/20 transition-all disabled:opacity-50"
              >
                {submitting ? 'Guardando...' : 'Guardar'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 rounded-lg bg-bg-tertiary/30 text-text-secondary text-xs hover:text-text-primary transition-colors"
              >
                Cancelar
              </button>
            </div>
          </form>
        )}

        {absences.length === 0 ? (
          <p className="text-xs text-text-secondary/50 text-center py-4">
            Sin bajas registradas. El modelo asume plantilla completa.
          </p>
        ) : (
          <div className="space-y-2">
            {absences.map(a => {
              const imp = IMPORTANCE_LABELS[a.importance] ?? IMPORTANCE_LABELS[2];
              return (
                <div key={a.id} className="flex items-center gap-3 p-2.5 rounded-xl bg-bg-tertiary/20">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-semibold text-text-primary">{a.player_name}</span>
                      {a.position && (
                        <span className="text-[9px] bg-bg-tertiary px-1.5 py-0.5 rounded text-text-secondary">
                          {POSITION_LABELS[a.position] ?? a.position}
                        </span>
                      )}
                      <span className={`text-[9px] font-semibold ${imp.color}`}>{imp.label}</span>
                    </div>
                    <span className="text-[10px] text-danger/70">
                      {REASON_LABELS[a.reason] ?? a.reason}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDeleteAbsence(a.id)}
                    className="p-1.5 rounded-lg text-text-secondary/40 hover:text-danger hover:bg-danger/10 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
            <p className="text-[10px] text-text-secondary/40 pt-1">
              Las bajas reducen las lambdas de Poisson del equipo automáticamente en el próximo cálculo.
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
