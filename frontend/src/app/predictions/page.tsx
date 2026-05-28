'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Zap, ChevronDown, ChevronUp, CheckCircle2, AlertCircle, Loader2, TrendingUp, RefreshCw, BookmarkPlus } from 'lucide-react';
import LoadingBall from '@/components/ui/LoadingBall';
import StatsCard from '@/components/ui/StatsCard';
import ProbabilityBar from '@/components/charts/ProbabilityBar';
import ScorelineMatrix from '@/components/charts/ScorelineMatrix';
import { api } from '@/lib/api';
import type { Match, AIPrediction } from '@/types';

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    pct >= 80 ? 'bg-success/15 text-success' :
    pct >= 65 ? 'bg-accent-amber/15 text-accent-amber' :
    'bg-danger/15 text-danger';
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${color}`}>
      {pct >= 80 ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
      {pct}% confianza
    </span>
  );
}

function LambdaBadge({ lambda, label }: { lambda: number; label: string }) {
  return (
    <div className="flex flex-col items-center px-3 py-2 rounded-xl bg-bg-tertiary/40">
      <span className="text-lg font-bold gradient-gold-text">{lambda.toFixed(2)}</span>
      <span className="text-[10px] text-text-secondary mt-0.5">λ {label}</span>
    </div>
  );
}

function FlagImg({ url, emoji, name }: { url?: string; emoji?: string; name: string }) {
  const [imgFailed, setImgFailed] = React.useState(false);
  if (url && !imgFailed) {
    return (
      <img
        src={url}
        alt={name}
        className="w-9 h-6 object-cover rounded-sm shadow-sm flex-shrink-0"
        onError={() => setImgFailed(true)}
      />
    );
  }
  return <span className="text-3xl flex-shrink-0">{emoji || '🏳️'}</span>;
}

export default function PredictionsPage() {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [matches, setMatches] = useState<any[]>([]);
  const [predictions, setPredictions] = useState<Record<number, AIPrediction>>({});
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set());
  const [savingId, setSavingId] = useState<number | null>(null);
  const [generatingIds, setGeneratingIds] = useState<Set<number>>(new Set());

  const loadPredictions = useCallback(async (force = false) => {
    try {
      const allMatches = await api.getUpcomingMatches();
      const upcomingData = (allMatches as any[]).slice(0, 10);
      setMatches(upcomingData);

      const preds: Record<number, AIPrediction> = {};
      for (const item of upcomingData) {
        const matchId = item.match.id;
        try {
          const p = await api.getAIPrediction(matchId, force);
          preds[matchId] = p;
        } catch {
          // prediction not yet available for this match
        }
      }
      setPredictions(preds);
    } catch (error) {
      console.error('Error loading predictions:', error);
    }
  }, []);

  useEffect(() => {
    async function init() {
      setLoading(true);
      await loadPredictions(false);
      setLoading(false);
    }
    init();
  }, [loadPredictions]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadPredictions(true);
    setRefreshing(false);
  };

  const handleGeneratePrediction = async (matchId: number) => {
    setGeneratingIds(prev => new Set(prev).add(matchId));
    try {
      const p = await api.getAIPrediction(matchId, true);
      setPredictions(prev => ({ ...prev, [matchId]: p }));
    } catch (err) {
      console.error('Error generando predicción:', err);
    } finally {
      setGeneratingIds(prev => { const s = new Set(prev); s.delete(matchId); return s; });
    }
  };

  const handleUsePrediction = async (matchId: number, homeScore: number, awayScore: number) => {
    setSavingId(matchId);
    try {
      await api.savePrediction({
        match_id: matchId,
        predicted_home_score: homeScore,
        predicted_away_score: awayScore,
      });
      setSavedIds(prev => new Set(prev).add(matchId));
    } catch (err) {
      console.error('Error guardando predicción:', err);
    } finally {
      setSavingId(null);
    }
  };

  const predList = Object.values(predictions);
  const avgConfidence =
    predList.length > 0
      ? Math.round((predList.reduce((s, p) => s + p.confidence_score, 0) / predList.length) * 100)
      : 0;
  const avgLambda =
    predList.length > 0
      ? ((predList.reduce((s, p) => s + (p.poisson_home_lambda ?? 0) + (p.poisson_away_lambda ?? 0), 0)) /
          (predList.length * 2)).toFixed(2)
      : '—';

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto h-[60vh] flex flex-col items-center justify-center gap-4">
        <LoadingBall text="Cargando predicciones Poisson + ELO..." />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-accent-gold/10">
            <Brain className="w-6 h-6 text-accent-gold" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-text-primary">
              Predicciones <span className="gradient-gold-text">IA + Poisson</span>
            </h1>
            <p className="text-text-secondary text-sm">
              Dixon-Coles + ELO + xG + DeepSeek V4 Pro
            </p>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-bg-secondary border border-accent-gold/20 text-accent-gold text-xs font-medium hover:bg-accent-gold/10 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Actualizando...' : 'Actualizar predicciones'}
        </button>
      </motion.div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatsCard icon={Zap} label="Confianza Promedio" value={`${avgConfidence}%`} color="gold" delay={0.1} />
        <StatsCard icon={TrendingUp} label="λ Promedio (goles esp.)" value={avgLambda} color="blue" delay={0.15} />
        <StatsCard icon={Brain} label="Partidos Analizados" value={predList.length} color="green" delay={0.2} />
      </div>

      {/* Predictions List */}
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-4">
        {matches.map((item: any) => {
          const match = item.match ?? item;
          const matchId = match.id;
          const pred = predictions[matchId];
          const isGenerating = generatingIds.has(matchId);
          const isExpanded = expandedId === matchId;

          // Card for matches without prediction yet
          if (!pred) {
            const homeName = item.home_team_name ?? '';
            const awayName = item.away_team_name ?? '';
            const homeFlag = item.home_team_flag ?? '';
            const awayFlag = item.away_team_flag ?? '';
            const date = match.match_date ? match.match_date.substring(0, 10) : '';
            return (
              <motion.div key={matchId} variants={item} layout className="rounded-2xl border border-white/5 bg-bg-secondary/40 backdrop-blur-xl overflow-hidden">
                <div className="p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{homeFlag}</span>
                    <span className="text-sm font-semibold text-text-primary">{homeName}</span>
                    <span className="text-text-secondary text-xs">vs</span>
                    <span className="text-sm font-semibold text-text-primary">{awayName}</span>
                    <span className="text-2xl">{awayFlag}</span>
                    <span className="text-xs text-text-secondary ml-2">{date}</span>
                  </div>
                  <button
                    onClick={() => handleGeneratePrediction(matchId)}
                    disabled={isGenerating}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-gold/10 border border-accent-gold/20 text-accent-gold text-xs font-medium hover:bg-accent-gold/20 transition-all disabled:opacity-50 flex-shrink-0"
                  >
                    {isGenerating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Brain className="w-3.5 h-3.5" />}
                    {isGenerating ? 'Generando con IA...' : 'Generar predicción IA'}
                  </button>
                </div>
              </motion.div>
            );
          }
          const homeName = item.home_team_name ?? (match as any).home_team_name;
          const awayName = item.away_team_name ?? (match as any).away_team_name;
          const homeFlag = item.home_team_flag ?? (match as any).home_flag;
          const awayFlag = item.away_team_flag ?? (match as any).away_flag;
          const homeFlagUrl = item.home_team_flag_url ?? '';
          const awayFlagUrl = item.away_team_flag_url ?? '';
          const date = match.match_date ? match.match_date.substring(0, 10) : '';

          return (
            <motion.div
              key={matchId}
              variants={item}
              layout
              className="rounded-2xl border border-accent-gold/10 bg-bg-secondary/60 backdrop-blur-xl overflow-hidden hover:border-accent-gold/20 hover:shadow-[0_0_25px_rgba(212,168,83,0.06)] transition-all duration-300"
            >
              <div className="p-5 sm:p-6">
                {/* Match Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-4 sm:gap-6">
                    <div className="text-center">
                      <div className="flex justify-center mb-1">
                        <FlagImg url={homeFlagUrl} emoji={homeFlag} name={homeName} />
                      </div>
                      <span className="text-xs font-semibold text-text-primary">{homeName}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-3xl font-bold gradient-gold-text">{pred.predicted_home_score}</span>
                      <span className="text-lg text-text-secondary">-</span>
                      <span className="text-3xl font-bold gradient-gold-text">{pred.predicted_away_score}</span>
                    </div>
                    <div className="text-center">
                      <div className="flex justify-center mb-1">
                        <FlagImg url={awayFlagUrl} emoji={awayFlag} name={awayName} />
                      </div>
                      <span className="text-xs font-semibold text-text-primary">{awayName}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <ConfidenceBadge confidence={pred.confidence_score} />
                    <span className="text-xs text-text-secondary">{date}</span>
                  </div>
                </div>

                {/* Lambda badges */}
                {(pred.poisson_home_lambda != null || pred.poisson_away_lambda != null) && (
                  <div className="mt-4 flex items-center gap-3">
                    <span className="text-[10px] text-text-secondary uppercase tracking-wider">λ esperados</span>
                    <LambdaBadge lambda={pred.poisson_home_lambda ?? 0} label={homeName} />
                    <LambdaBadge lambda={pred.poisson_away_lambda ?? 0} label={awayName} />
                  </div>
                )}

                {/* Probability Bar */}
                <div className="mt-4">
                  <ProbabilityBar
                    homeWin={pred.home_win_prob}
                    draw={pred.draw_prob}
                    awayWin={pred.away_win_prob}
                    homeTeam={homeName}
                    awayTeam={awayName}
                  />
                </div>

                {/* Expand/Collapse + Use Prediction */}
                <div className="mt-4 flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : matchId)}
                      className="flex items-center gap-1.5 text-xs text-accent-gold hover:text-accent-amber transition-colors font-medium"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      {isExpanded ? 'Ocultar análisis' : 'Ver análisis + matriz'}
                    </button>
                    <button
                      onClick={() => handleGeneratePrediction(matchId)}
                      disabled={isGenerating}
                      className="flex items-center gap-1 text-xs text-text-secondary hover:text-accent-gold transition-colors disabled:opacity-40"
                      title="Regenerar con DeepSeek"
                    >
                      {isGenerating ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                      {isGenerating ? 'Generando...' : 'Regenerar'}
                    </button>
                  </div>
                  {savedIds.has(matchId) ? (
                    <span className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-success/15 text-success text-xs font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Guardada en polla
                    </span>
                  ) : (
                    <button
                      onClick={() => handleUsePrediction(matchId, pred.predicted_home_score, pred.predicted_away_score)}
                      disabled={savingId === matchId}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-accent-gold to-accent-amber text-bg-primary text-xs font-semibold hover:shadow-[0_0_20px_rgba(212,168,83,0.3)] transition-shadow disabled:opacity-60"
                    >
                      {savingId === matchId ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <BookmarkPlus className="w-3.5 h-3.5" />
                      )}
                      Usar en mi polla
                    </button>
                  )}
                </div>
              </div>

              {/* Expanded Content */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="px-5 sm:px-6 pb-5 sm:pb-6 border-t border-accent-gold/10 pt-5 space-y-6">

                      {/* Scoreline Matrix */}
                      {pred.scoreline_matrix && pred.scoreline_matrix.length > 0 && (
                        <div className="rounded-xl bg-bg-tertiary/20 p-4">
                          <ScorelineMatrix
                            matrix={pred.scoreline_matrix}
                            homeTeam={homeName}
                            awayTeam={awayName}
                            predictedHome={pred.predicted_home_score}
                            predictedAway={pred.predicted_away_score}
                          />
                        </div>
                      )}

                      {/* Analysis Text */}
                      <div>
                        <h4 className="text-xs font-semibold text-accent-gold uppercase tracking-wider mb-2">
                          Análisis DeepSeek
                        </h4>
                        <p className="text-sm text-text-secondary leading-relaxed">{pred.analysis_text}</p>
                      </div>

                      {/* Factors */}
                      {pred.factors && pred.factors.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-accent-gold uppercase tracking-wider mb-2">
                            Factores Clave
                          </h4>
                          <div className="space-y-2">
                            {pred.factors.map((factor, idx) => (
                              <div key={idx} className="flex items-start gap-2.5 p-2.5 rounded-lg bg-bg-tertiary/30">
                                <span className="w-1.5 h-1.5 rounded-full bg-accent-gold flex-shrink-0 mt-1.5" />
                                <p className="text-xs text-text-secondary">
                                  {typeof factor === 'string' ? factor : (factor as any).description ?? JSON.stringify(factor)}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
