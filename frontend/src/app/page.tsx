'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Calendar, Clock, Trophy, Target, Brain,
  ChevronRight, Sparkles, GitBranch, Zap, Activity,
} from 'lucide-react';
import Link from 'next/link';
import StatsCard from '@/components/ui/StatsCard';
import FlagImg from '@/components/ui/FlagImg';
import LoadingBall from '@/components/ui/LoadingBall';
import { api } from '@/lib/api';
import { matchLocalDate, matchLocalTime, matchLocalDateLabel } from '@/lib/datetime';
import type { Match } from '@/types';

const WC_START = new Date('2026-06-11T18:00:00Z');

function tournamentStarted() {
  return Date.now() >= WC_START.getTime();
}

function tournamentDay() {
  return Math.max(1, Math.floor((Date.now() - WC_START.getTime()) / 86400000) + 1);
}

/** Polla scoring: 3 = marcador exacto, 1 = resultado correcto, 0 = fallo. */
function pollaPoints(ph: number, pa: number, ah: number, aa: number): number {
  if (ph === ah && pa === aa) return 3;
  const pred = ph > pa ? 1 : ph < pa ? -1 : 0;
  const actual = ah > aa ? 1 : ah < aa ? -1 : 0;
  return pred === actual ? 1 : 0;
}

const stagger = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' as const } },
};

function CountdownHero({ target }: { target: Date }) {
  const [t, setT] = useState({ d: 0, h: 0, m: 0, s: 0 });
  useEffect(() => {
    const tick = () => {
      const diff = target.getTime() - Date.now();
      if (diff > 0) setT({
        d: Math.floor(diff / 86400000),
        h: Math.floor((diff % 86400000) / 3600000),
        m: Math.floor((diff % 3600000) / 60000),
        s: Math.floor((diff % 60000) / 1000),
      });
      else setT({ d: 0, h: 0, m: 0, s: 0 });
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [target]);

  return (
    <div className="flex items-center gap-3 sm:gap-4">
      {[{ v: t.d, l: 'DÍAS' }, { v: t.h, l: 'HRS' }, { v: t.m, l: 'MIN' }, { v: t.s, l: 'SEG' }].map(({ v, l }) => (
        <div key={l} className="flex flex-col items-center">
          <div
            className="w-14 sm:w-16 h-14 sm:h-16 rounded-2xl flex items-center justify-center stat-value"
            style={{
              background: 'linear-gradient(135deg, rgba(224,180,74,0.12), rgba(224,180,74,0.05))',
              border: '1px solid rgba(224,180,74,0.2)',
              boxShadow: '0 4px 16px rgba(0,0,0,0.2), 0 0 20px rgba(224,180,74,0.06) inset',
              fontSize: '1.5rem',
              fontWeight: 800,
              color: '#f0c060',
              letterSpacing: '-0.04em',
            }}
          >
            {String(v).padStart(2, '0')}
          </div>
          <span className="text-[9px] text-text-muted uppercase tracking-[0.15em] mt-1.5">{l}</span>
        </div>
      ))}
    </div>
  );
}

function AIInsight({ text, loading }: { text: string; loading: boolean }) {
  const [display, setDisplay] = useState('');
  useEffect(() => {
    if (!text) return;
    setDisplay('');
    let i = 0;
    const id = setInterval(() => {
      if (i < text.length) { setDisplay(text.slice(0, ++i)); }
      else clearInterval(id);
    }, 14);
    return () => clearInterval(id);
  }, [text]);

  if (loading) return (
    <div className="space-y-2.5">
      {[95, 82, 68].map(w => (
        <div key={w} className="h-3 rounded-lg bg-white/[0.04] animate-pulse" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
  return (
    <p className="text-text-secondary text-sm leading-relaxed">
      {display}
      {display.length < text.length && <span className="animate-pulse text-accent-gold ml-0.5">▌</span>}
    </p>
  );
}

export default function DashboardPage() {
  const [loading, setLoading]         = useState(true);
  const [upcoming, setUpcoming]       = useState<Match[]>([]);
  const [results, setResults]         = useState<any[]>([]);
  const [playedCount, setPlayed]      = useState(0);
  const [aiByMatch, setAiByMatch]     = useState<Record<number, any>>({});
  const [groups, setGroups]           = useState<{ group: string; teams: any[] }[]>([]);
  const [stats, setStats]             = useState<any>(null);
  const [insight, setInsight]         = useState('');
  const [insightLoading, setIL]       = useState(true);
  const [favorites, setFavorites]     = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      // allSettled: si un endpoint falla, el resto del dashboard sigue funcionando
      const [matchesR, statsR, gAR, gCR, gER, completedR] = await Promise.allSettled([
        api.getUpcomingMatches(),
        api.getPredictionStats(),
        api.getGroupAnalysis('A'),
        api.getGroupAnalysis('C'),
        api.getGroupAnalysis('E'),
        api.getMatches({ status: 'completed' }),
      ]);

      const mapMatch = (item: any) => ({
        ...item.match,
        home_team: item.match.home_team_code,
        away_team: item.match.away_team_code,
        home_team_name: item.home_team_name,
        away_team_name: item.away_team_name,
        home_flag: item.home_team_flag,
        away_flag: item.away_team_flag,
        home_flag_url: item.home_team_flag_url ?? '',
        away_flag_url: item.away_team_flag_url ?? '',
        date: matchLocalDate(item.match.match_date),
        time: matchLocalTime(item.match.match_date),
      });

      if (matchesR.status === 'fulfilled') {
        setUpcoming((matchesR.value as any[]).map(mapMatch).slice(0, 5));
      }
      if (statsR.status === 'fulfilled') setStats(statsR.value);

      let recent: any[] = [];
      if (completedR.status === 'fulfilled') {
        const completed = (completedR.value as any[]).map(mapMatch);
        setPlayed(completed.length);
        recent = completed
          .sort((a, b) => String(b.match_date).localeCompare(String(a.match_date)))
          .slice(0, 5);
        setResults(recent);
      }

      const buildGroups = (letter: string, data: any) => ({
        group: letter,
        teams: data.predicted_standings.map((s: any) => ({
          ...s,
          flag: data.teams.find((t: any) => t.code === s.team_code)?.flag_emoji ?? '🏳️',
        })),
      });
      setGroups(
        ([['A', gAR], ['C', gCR], ['E', gER]] as const)
          .filter(([, r]) => r.status === 'fulfilled')
          .map(([letter, r]) => buildGroups(letter, (r as PromiseFulfilledResult<any>).value))
      );

      setLoading(false);

      // Predicciones IA cacheadas de los resultados recientes (sin LLM) para
      // mostrar aciertos del modelo + construir el insight del día.
      const statsCalls = await Promise.allSettled(recent.map(m => api.getMatchStats(m.id)));
      const aiMap: Record<number, any> = {};
      statsCalls.forEach((r, i) => {
        const ai = r.status === 'fulfilled' ? (r.value as any)?.ai_prediction : null;
        if (ai) aiMap[recent[i].id] = ai;
      });
      setAiByMatch(aiMap);

      const scored = recent.filter(m => aiMap[m.id]);
      const outcomeHits = scored.filter(m => pollaPoints(
        aiMap[m.id].predicted_home_score, aiMap[m.id].predicted_away_score,
        m.home_score, m.away_score,
      ) >= 1).length;
      const exactHits = scored.filter(m => pollaPoints(
        aiMap[m.id].predicted_home_score, aiMap[m.id].predicted_away_score,
        m.home_score, m.away_score,
      ) === 3).length;

      if (scored.length > 0) {
        setInsight(
          `¡El Mundial 2026 está en marcha! El modelo ha acertado el resultado en ${outcomeHits} de ${scored.length} partidos jugados` +
          (exactHits > 0 ? `, incluyendo ${exactHits} marcador${exactHits > 1 ? 'es' : ''} exacto${exactHits > 1 ? 's' : ''}` : '') +
          `. Las probabilidades se recalculan automáticamente con cada resultado: ELO, forma y tablas de grupo ya reflejan lo jugado.`
        );
      } else {
        const gA = gAR.status === 'fulfilled' ? (gAR as PromiseFulfilledResult<any>).value : null;
        const top = gA?.predicted_standings?.slice(0, 3).map((t: any) => t.team_name).join(', ') ?? '';
        setInsight(top
          ? `Análisis del Grupo A: ${top} lideran según el modelo Poisson + ELO. El modelo recalcula probabilidades con cada resultado real del torneo.`
          : 'El modelo estadístico analiza el torneo usando Poisson, ELO y xG histórico, y se actualiza automáticamente con cada resultado real.'
        );
      }
      setIL(false);

      api.getTournamentSimulation(1000)
        .then((sim: any) => setFavorites((sim.teams ?? []).slice(0, 5)))
        .catch(() => {});
    })();
  }, []);

  const nextMatch: any = upcoming[0] ?? null;
  const started = tournamentStarted();

  if (loading) return (
    <div className="max-w-7xl mx-auto h-[60vh] flex items-center justify-center">
      <LoadingBall text="Cargando dashboard..." />
    </div>
  );

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="max-w-7xl mx-auto space-y-8">

      {/* ── HERO SECTION ── */}
      <motion.div
        variants={fadeUp}
        className="relative overflow-hidden rounded-3xl p-7 sm:p-10"
        style={{
          background: 'linear-gradient(135deg, rgba(15,12,30,0.95) 0%, rgba(12,12,22,0.92) 50%, rgba(8,8,16,0.95) 100%)',
          border: '1px solid rgba(224,180,74,0.14)',
          boxShadow: '0 24px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.02) inset',
        }}
      >
        {/* Background glow orbs */}
        <div className="absolute -top-24 -left-24 w-72 h-72 rounded-full opacity-20 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(224,180,74,0.3), transparent 70%)' }} />
        <div className="absolute -bottom-20 -right-20 w-64 h-64 rounded-full opacity-10 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.4), transparent 70%)' }} />
        <div className="absolute top-0 left-0 right-0 h-px"
          style={{ background: 'linear-gradient(90deg, transparent, rgba(224,180,74,0.4), transparent)' }} />

        <div className="relative flex flex-col lg:flex-row lg:items-center gap-8">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <span className="badge badge-gold">
                <Activity className="w-2.5 h-2.5" /> {started ? `Mundial en curso · Día ${tournamentDay()}` : 'Sistema activo'}
              </span>
              <span className="badge badge-purple">
                <Zap className="w-2.5 h-2.5" /> IA en línea
              </span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-black leading-none mb-2" style={{ letterSpacing: '-0.03em' }}>
              <span className="gradient-gold-text">FIFA World</span>
              <br />
              <span className="text-text-primary">Cup 2026</span>
            </h1>
            <p className="text-text-secondary text-sm mt-3 max-w-md leading-relaxed">
              Panel de análisis en tiempo real · Predicciones con modelo Poisson + ELO + Monte Carlo
            </p>
            <div className="flex items-center gap-3 mt-5">
              <Link
                href="/predictions"
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.03]"
                style={{ background: 'linear-gradient(135deg, #e0b44a, #f59e0b)', color: '#0a0a0f', boxShadow: '0 4px 20px rgba(224,180,74,0.3)' }}
              >
                <Brain className="w-4 h-4" /> Predecir ahora
              </Link>
              <Link
                href="/bracket"
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-text-secondary hover:text-text-primary transition-all duration-200 border border-white/[0.07] hover:border-white/[0.14]"
                style={{ background: 'rgba(255,255,255,0.04)' }}
              >
                <GitBranch className="w-4 h-4" /> Ver simulación
              </Link>
            </div>
          </div>

          <div className="flex flex-col items-center gap-3">
            {started && nextMatch ? (
              <>
                <p className="text-[10px] text-text-muted uppercase tracking-[0.18em]">Próximo partido</p>
                <CountdownHero target={new Date(nextMatch.match_date)} />
                <p className="text-xs text-text-secondary">
                  {nextMatch.home_team_name} vs {nextMatch.away_team_name} · {matchLocalDateLabel(nextMatch.match_date)}, {nextMatch.time}
                </p>
              </>
            ) : (
              <>
                <p className="text-[10px] text-text-muted uppercase tracking-[0.18em]">{started ? 'Mundial en curso' : 'Inicio del torneo'}</p>
                <CountdownHero target={WC_START} />
                <p className="text-xs text-text-secondary">11 Jun 2026 · Ciudad de México</p>
              </>
            )}
          </div>
        </div>
      </motion.div>

      {/* ── STATS CARDS ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard icon={Calendar} label="Partidos Jugados" value={`${playedCount}/104`}            color="blue"  delay={0.05} />
        <StatsCard icon={Clock}    label="Próximo Partido" value={<CountdownClockMini target={nextMatch ? new Date(nextMatch.match_date) : null} />} color="amber" delay={0.10} />
        <StatsCard icon={Trophy}   label="Mis Puntos"      value={stats?.total_points ?? 0}         color="gold"  delay={0.15} trend={stats?.total_points ? { value: 12, positive: true } : undefined} />
        <StatsCard icon={Target}   label="Precisión"       value={`${stats?.accuracy_pct ?? 0}%`}   color="green" delay={0.20} />
      </div>

      {/* ── ROW 2: Upcoming + Chart ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Upcoming matches */}
        <motion.div variants={fadeUp} className="card-premium rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="section-title">
              <Calendar className="w-4.5 h-4.5" />
              Próximos Partidos
            </h2>
            <Link href="/matches" className="flex items-center gap-1 text-xs text-accent-gold/80 hover:text-accent-gold transition-colors">
              Ver todos <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-2">
            {upcoming.map((m, i) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.25 + i * 0.07 }}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl group transition-colors"
                style={{ background: 'rgba(255,255,255,0.025)' }}
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <FlagImg url={(m as any).home_flag_url} emoji={(m as any).home_flag} teamCode={(m as any).home_team} name={(m as any).home_team_name} size="sm" />
                  <span className="text-xs font-medium text-text-primary truncate">{(m as any).home_team_name}</span>
                  <span className="text-[10px] font-bold text-accent-gold/70 mx-1 flex-shrink-0">vs</span>
                  <span className="text-xs font-medium text-text-primary truncate">{(m as any).away_team_name}</span>
                  <FlagImg url={(m as any).away_flag_url} emoji={(m as any).away_flag} teamCode={(m as any).away_team} name={(m as any).away_team_name} size="sm" />
                </div>
                <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                  <span className="text-[10px] text-text-muted hidden sm:block">{m.date}</span>
                  <Link
                    href="/predictions"
                    className="opacity-0 group-hover:opacity-100 transition-opacity px-2.5 py-1 rounded-lg text-[10px] font-semibold text-accent-gold"
                    style={{ background: 'rgba(224,180,74,0.1)', border: '1px solid rgba(224,180,74,0.15)' }}
                  >
                    Predecir
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Recent results + model performance */}
        <motion.div variants={fadeUp} className="card-premium rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="section-title">
              <Activity className="w-4.5 h-4.5" />
              Resultados Recientes
            </h2>
            <Link href="/matches" className="flex items-center gap-1 text-xs text-accent-gold/80 hover:text-accent-gold transition-colors">
              Ver todos <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {results.length === 0 ? (
            <p className="text-xs text-text-muted">Aún no hay partidos finalizados.</p>
          ) : (
            <div className="space-y-2">
              {results.map((m, i) => {
                const ai = aiByMatch[m.id];
                const pts = ai ? pollaPoints(ai.predicted_home_score, ai.predicted_away_score, m.home_score, m.away_score) : null;
                return (
                  <motion.div
                    key={m.id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.25 + i * 0.07 }}
                    className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl"
                    style={{ background: 'rgba(255,255,255,0.025)' }}
                  >
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <FlagImg url={m.home_flag_url} emoji={m.home_flag} teamCode={m.home_team} name={m.home_team_name} size="sm" />
                      <span className="text-xs font-medium text-text-primary truncate">{m.home_team_name}</span>
                      <span className="text-xs font-bold text-accent-gold mx-1 flex-shrink-0 tabular-nums">
                        {m.home_score} - {m.away_score}
                      </span>
                      <span className="text-xs font-medium text-text-primary truncate">{m.away_team_name}</span>
                      <FlagImg url={m.away_flag_url} emoji={m.away_flag} teamCode={m.away_team} name={m.away_team_name} size="sm" />
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                      {pts !== null && (
                        <span
                          className="px-2 py-0.5 rounded-md text-[10px] font-semibold"
                          style={pts === 3
                            ? { background: 'rgba(224,180,74,0.12)', border: '1px solid rgba(224,180,74,0.25)', color: '#f0c060' }
                            : pts === 1
                              ? { background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', color: '#4ade80' }
                              : { background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171' }}
                          title={`La IA predijo ${ai.predicted_home_score}-${ai.predicted_away_score}`}
                        >
                          {pts === 3 ? 'IA: exacto' : pts === 1 ? 'IA: acertó' : 'IA: falló'}
                        </span>
                      )}
                      <span className="text-[10px] text-text-muted hidden sm:block">{m.date}</span>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>
      </div>

      {/* ── ROW 3: AI Insight + Groups ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* AI Insight */}
        <motion.div
          variants={fadeUp}
          className="relative rounded-2xl p-6 overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, rgba(18,14,34,0.95) 0%, rgba(14,14,26,0.9) 100%)',
            border: '1px solid rgba(224,180,74,0.14)',
          }}
        >
          <div className="absolute inset-0 pointer-events-none"
            style={{ background: 'radial-gradient(ellipse 80% 60% at 0% 0%, rgba(139,92,246,0.05), transparent)' }} />
          <div className="absolute top-0 left-0 right-0 h-px"
            style={{ background: 'linear-gradient(90deg, transparent, rgba(224,180,74,0.3), transparent)' }} />

          <div className="relative">
            <div className="flex items-start gap-3 mb-4">
              <div className="p-2.5 rounded-xl flex-shrink-0" style={{ background: 'rgba(224,180,74,0.1)', border: '1px solid rgba(224,180,74,0.15)' }}>
                <Brain className="w-5 h-5 text-accent-gold" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                  Insight IA del Día
                  <Sparkles className="w-3.5 h-3.5 text-accent-amber" />
                </h2>
                <p className="text-[10px] text-text-muted mt-0.5">Análisis automatizado · Modelo v3.2</p>
              </div>
            </div>

            <AIInsight text={insight} loading={insightLoading} />

            <div className="flex items-center gap-2 mt-4 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              <span className="badge badge-gold">Poisson + ELO</span>
              <span className="badge badge-purple">DeepSeek v4</span>
              <span className="badge badge-blue">xG Model</span>
            </div>
          </div>
        </motion.div>

        {/* Featured Groups */}
        <motion.div variants={fadeUp} className="card-premium rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="section-title">
              <Trophy className="w-4.5 h-4.5" />
              Grupos Destacados
            </h2>
            <Link href="/groups" className="flex items-center gap-1 text-xs text-accent-gold/80 hover:text-accent-gold transition-colors">
              Ver todos <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-4">
            {groups.map(g => (
              <div key={g.group}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] font-bold text-accent-gold/80 uppercase tracking-wider px-2 py-0.5 rounded-md"
                    style={{ background: 'rgba(224,180,74,0.08)', border: '1px solid rgba(224,180,74,0.12)' }}>
                    Grupo {g.group}
                  </span>
                </div>
                <div className="space-y-1">
                  {g.teams.map((t, i) => (
                    <div
                      key={t.team_code}
                      className="flex items-center justify-between px-2.5 py-1.5 rounded-lg"
                      style={{
                        background: i < 2 ? 'rgba(34,197,94,0.05)' : 'transparent',
                        borderLeft: i < 2 ? '2px solid rgba(34,197,94,0.4)' : '2px solid transparent',
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-text-muted w-3 text-center font-bold">{i + 1}</span>
                        <FlagImg emoji={t.flag} teamCode={t.team_code} name={t.team_name} size="sm" />
                        <span className="text-xs font-medium text-text-primary">{t.team_name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] text-text-muted">{t.wins}V {t.draws}E {t.losses}D</span>
                        <span className="text-xs font-bold text-text-primary w-5 text-right tabular-nums">{t.points}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* ── ROW 4: Monte Carlo Favorites ── */}
      {favorites.length > 0 && (
        <motion.div variants={fadeUp} className="card-premium rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="section-title">
                <GitBranch className="w-4.5 h-4.5" />
                Favoritos al Título
              </h2>
              <p className="text-[10px] text-text-muted mt-0.5 ml-6">Simulación Monte Carlo · 1,000 torneos</p>
            </div>
            <Link href="/bracket" className="flex items-center gap-1 text-xs text-accent-gold/80 hover:text-accent-gold transition-colors">
              Simulación completa <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3.5">
            {favorites.map((team, i) => (
              <div key={team.team_code} className="flex items-center gap-4">
                <span
                  className="text-xs font-black w-6 text-center flex-shrink-0 stat-value"
                  style={{ color: i === 0 ? '#e0b44a' : i === 1 ? '#9ca3af' : i === 2 ? '#cd7f32' : '#4a4a62' }}
                >
                  {i + 1}
                </span>
                <FlagImg emoji={team.flag_emoji} teamCode={team.team_code} name={team.team_name} size="sm" />
                <span className="text-sm font-medium text-text-primary flex-1 min-w-0 truncate">{team.team_name}</span>
                <div className="flex items-center gap-3 min-w-[140px]">
                  <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: i === 0 ? 'linear-gradient(90deg, #e0b44a, #f59e0b)' : 'rgba(224,180,74,0.5)' }}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min((team.p_champion / (favorites[0]?.p_champion || 1)) * 100, 100)}%` }}
                      transition={{ duration: 0.9, delay: 0.3 + i * 0.1, ease: 'easeOut' as const }}
                    />
                  </div>
                  <span className="text-sm font-bold text-accent-gold tabular-nums w-11 text-right stat-value">
                    {team.p_champion}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

function CountdownClockMini({ target }: { target: Date | null }) {
  const [t, setT] = useState({ d: 0, h: 0, m: 0, s: 0 });
  useEffect(() => {
    if (!target) return;
    const tick = () => {
      const diff = target.getTime() - Date.now();
      if (diff > 0) setT({
        d: Math.floor(diff / 86400000),
        h: Math.floor((diff % 86400000) / 3600000),
        m: Math.floor((diff % 3600000) / 60000),
        s: Math.floor((diff % 60000) / 1000),
      });
      else setT({ d: 0, h: 0, m: 0, s: 0 });
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [target?.getTime()]);
  if (!target) return <span className="font-mono text-3xl stat-value">—</span>;
  return (
    <span className="font-mono text-3xl stat-value">
      {t.d}<span className="text-text-muted text-lg">d </span>
      {String(t.h).padStart(2,'0')}<span className="text-text-muted">:</span>
      {String(t.m).padStart(2,'0')}<span className="text-text-muted">:</span>
      {String(t.s).padStart(2,'0')}
    </span>
  );
}
