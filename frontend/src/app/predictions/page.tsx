'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Zap, ChevronDown, ChevronUp, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import StatsCard from '@/components/ui/StatsCard';
import ProbabilityBar from '@/components/charts/ProbabilityBar';
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
  const color = pct >= 85 ? 'bg-success/15 text-success' : pct >= 70 ? 'bg-accent-amber/15 text-accent-amber' : 'bg-danger/15 text-danger';

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${color}`}>
      {pct >= 85 ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
      {pct}%
    </span>
  );
}

function ImpactDot({ impact }: { impact: 'positive' | 'negative' | 'neutral' }) {
  const colors = {
    positive: 'bg-success',
    negative: 'bg-danger',
    neutral: 'bg-text-secondary',
  };
  return <span className={`w-2 h-2 rounded-full ${colors[impact]} flex-shrink-0`} />;
}

export default function PredictionsPage() {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [matches, setMatches] = useState<Match[]>([]);
  const [predictions, setPredictions] = useState<Record<number, AIPrediction>>({});
  
  useEffect(() => {
    async function loadData() {
      try {
        // Obtenemos los próximos 3 partidos para analizar
        const allMatches = await api.getUpcomingMatches();
        const upcomingData = allMatches.slice(0, 3);
        
        const upcoming = (upcomingData as any[]).map(item => ({
          ...item.match,
          home_team_name: item.home_team_name,
          away_team_name: item.away_team_name,
          home_flag: item.home_team_flag,
          away_flag: item.away_team_flag,
          date: item.match.match_date ? item.match.match_date.substring(0, 10) : '',
        }));
        
        setMatches(upcoming);
        
        const preds: Record<number, AIPrediction> = {};
        for (const m of upcoming) {
          try {
            const p = await api.getAIPrediction(m.id);
            preds[m.id] = p;
          } catch (e) {
            console.error(`No AI prediction for match ${m.id}`, e);
          }
        }
        setPredictions(preds);
      } catch (error) {
        console.error('Error loading predictions:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const predList = Object.values(predictions);
  const avgConfidence = predList.length > 0
    ? Math.round((predList.reduce((sum, p) => sum + p.confidence_score, 0) / predList.length) * 100)
    : 0;

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto h-[60vh] flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-12 h-12 text-accent-gold animate-spin" />
        <p className="text-text-secondary font-medium animate-pulse">DeepSeek está analizando los datos climatológicos...</p>
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
          <Brain className="w-6 h-6 text-accent-gold" />
        </div>
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary">
            Predicciones <span className="gradient-gold-text">AI 🤖</span>
          </h1>
          <p className="text-text-secondary text-sm">Análisis inteligente potenciado por modelos de lenguaje avanzados</p>
        </div>
      </motion.div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatsCard icon={Zap} label="Confianza Promedio" value={`${avgConfidence}%`} color="gold" delay={0.1} />
        <StatsCard icon={CheckCircle2} label="Aciertos AI" value="0/0" trend={{ value: 0, positive: true }} color="green" delay={0.15} />
        <StatsCard icon={Brain} label="Partidos Analizados" value={predList.length} color="blue" delay={0.2} />
      </div>

      {/* Predictions List */}
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-4">
        {matches.map((match) => {
          const pred = predictions[match.id];
          if (!pred) return null;
          
          const isExpanded = expandedId === match.id;

          return (
            <motion.div
              key={match.id}
              variants={item}
              layout
              className="rounded-2xl border border-accent-gold/10 bg-bg-secondary/60 backdrop-blur-xl overflow-hidden transition-all duration-300 hover:border-accent-gold/20 hover:shadow-[0_0_25px_rgba(212,168,83,0.06)]"
            >
              <div className="p-5 sm:p-6">
                {/* Match header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  {/* Teams + Score */}
                  <div className="flex items-center gap-4 sm:gap-6">
                    {/* Home */}
                    <div className="text-center">
                      <span className="text-3xl block mb-1">{(match as any).home_team_flag || (match as any).home_flag || '🏠'}</span>
                      <span className="text-xs font-medium text-text-primary">{(match as any).home_team_name}</span>
                    </div>

                    {/* Predicted Score */}
                    <div className="flex items-center gap-2">
                      <span className="text-3xl font-bold gradient-gold-text">{pred.predicted_home_score}</span>
                      <span className="text-lg text-text-secondary">-</span>
                      <span className="text-3xl font-bold gradient-gold-text">{pred.predicted_away_score}</span>
                    </div>

                    {/* Away */}
                    <div className="text-center">
                      <span className="text-3xl block mb-1">{(match as any).away_team_flag || (match as any).away_flag || '✈️'}</span>
                      <span className="text-xs font-medium text-text-primary">{(match as any).away_team_name}</span>
                    </div>
                  </div>

                  {/* Confidence + Date */}
                  <div className="flex items-center gap-3">
                    <ConfidenceBadge confidence={pred.confidence_score} />
                    <span className="text-xs text-text-secondary">{match.match_date?.substring(0, 10) || match.date}</span>
                  </div>
                </div>

                {/* Probability Bar */}
                <div className="mt-5">
                  <ProbabilityBar
                    homeWin={pred.home_win_prob}
                    draw={pred.draw_prob}
                    awayWin={pred.away_win_prob}
                    homeTeam={(match as any).home_team_name}
                    awayTeam={(match as any).away_team_name}
                  />
                </div>

                {/* Expand/collapse button */}
                <div className="mt-4 flex items-center justify-between">
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : match.id)}
                    className="flex items-center gap-1.5 text-xs text-accent-gold hover:text-accent-amber transition-colors font-medium"
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    {isExpanded ? 'Ocultar análisis' : 'Ver análisis completo'}
                  </button>

                  <button className="px-4 py-2 rounded-xl bg-gradient-to-r from-accent-gold to-accent-amber text-bg-primary text-xs font-semibold hover:shadow-[0_0_20px_rgba(212,168,83,0.3)] transition-shadow">
                    Usar predicción
                  </button>
                </div>
              </div>

              {/* Expanded Analysis */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="px-5 sm:px-6 pb-5 sm:pb-6 border-t border-accent-gold/10 pt-5 space-y-4">
                      {/* Analysis Text */}
                      <div>
                        <h4 className="text-xs font-semibold text-accent-gold uppercase tracking-wider mb-2">Análisis de DeepSeek</h4>
                        <p className="text-sm text-text-secondary leading-relaxed">{pred.analysis_text}</p>
                      </div>

                      {/* Factors */}
                      {pred.factors && pred.factors.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-accent-gold uppercase tracking-wider mb-2">Factores Clave</h4>
                          <div className="space-y-2">
                            {pred.factors.map((factor, idx) => (
                              <div key={idx} className="flex items-start gap-2.5 p-2.5 rounded-lg bg-bg-tertiary/30">
                                <ImpactDot impact="neutral" />
                                <div className="flex-1 min-w-0">
                                  <p className="text-xs text-text-secondary mt-0.5">{typeof factor === 'string' ? factor : (factor as any).description || JSON.stringify(factor)}</p>
                                </div>
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
