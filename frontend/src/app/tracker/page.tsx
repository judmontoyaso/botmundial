'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Trophy,
  Target,
  CheckCircle2,
  Award,
  TrendingUp,
  Plus,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import StatsCard from '@/components/ui/StatsCard';
import { mockMyPredictions, mockPredictionStats, mockMatches } from '@/lib/mock-data';

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

function PointsBadge({ points }: { points: number | null }) {
  if (points === null) {
    return (
      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-bg-tertiary/50 text-text-secondary">
        Pendiente
      </span>
    );
  }
  if (points === 3) {
    return (
      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-success/15 text-success">
        +3 Exacto
      </span>
    );
  }
  if (points === 1) {
    return (
      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-accent-amber/15 text-accent-amber">
        +1 Ganador
      </span>
    );
  }
  return (
    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-danger/15 text-danger">
      0 Errado
    </span>
  );
}

export default function TrackerPage() {
  const [showForm, setShowForm] = useState(false);
  const [formMatchId, setFormMatchId] = useState('');
  const [formHome, setFormHome] = useState('');
  const [formAway, setFormAway] = useState('');
  const [formNotes, setFormNotes] = useState('');

  const scheduledMatches = mockMatches.filter(m => m.status === 'scheduled');
  const resolvedPredictions = mockMyPredictions.filter(p => p.points !== null);
  const pendingPredictions = mockMyPredictions.filter(p => p.points === null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In real app, this would call the API
    setShowForm(false);
    setFormMatchId('');
    setFormHome('');
    setFormAway('');
    setFormNotes('');
  };

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
            <Target className="w-6 h-6 text-accent-gold" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-text-primary">
              Mi <span className="gradient-gold-text">Polla Mundialista</span>
            </h1>
            <p className="text-text-secondary text-sm">Seguimiento de tus predicciones y puntos</p>
          </div>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-accent-gold to-accent-amber text-bg-primary text-sm font-semibold hover:shadow-[0_0_20px_rgba(212,168,83,0.3)] transition-all"
        >
          <Plus className="w-4 h-4" />
          Nueva Predicción
        </button>
      </motion.div>

      {/* Big Points Display */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="relative rounded-2xl border border-accent-gold/15 bg-bg-secondary/60 backdrop-blur-xl p-8 text-center overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-accent-gold/[0.04] to-transparent pointer-events-none" />
        <div className="relative">
          <Trophy className="w-12 h-12 text-accent-gold mx-auto mb-3 animate-float" />
          <p className="text-6xl sm:text-7xl font-bold gradient-gold-text text-glow-gold">
            {mockPredictionStats.total_points}
          </p>
          <p className="text-text-secondary text-sm mt-2">Puntos Totales</p>
        </div>
      </motion.div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatsCard icon={Target} label="Total Predicciones" value={mockPredictionStats.total_predictions} color="blue" delay={0.15} />
        <StatsCard icon={CheckCircle2} label="Exactos (3pts)" value={mockPredictionStats.exact_scores} color="green" delay={0.2} />
        <StatsCard icon={Award} label="Ganador (1pt)" value={mockPredictionStats.correct_winner} color="amber" delay={0.25} />
        <StatsCard icon={TrendingUp} label="Precisión" value={`${mockPredictionStats.accuracy}%`} trend={{ value: 8, positive: true }} color="gold" delay={0.3} />
      </div>

      {/* Points Chart */}
      <motion.div variants={item} initial="hidden" animate="show" className="rounded-2xl border border-accent-gold/10 bg-bg-secondary/60 backdrop-blur-xl p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-5 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-accent-gold" />
          Evolución de Puntos
        </h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mockPredictionStats.points_history}>
              <defs>
                <linearGradient id="lineGold" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#d4a853" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#d4a853" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(136,136,160,0.1)" />
              <XAxis dataKey="matchday" tick={{ fill: '#8888a0', fontSize: 12 }} axisLine={{ stroke: 'rgba(136,136,160,0.2)' }} tickLine={false} label={{ value: 'Jornada', position: 'insideBottom', offset: -5, fill: '#8888a0', fontSize: 11 }} />
              <YAxis tick={{ fill: '#8888a0', fontSize: 12 }} axisLine={{ stroke: 'rgba(136,136,160,0.2)' }} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#12121a',
                  border: '1px solid rgba(212,168,83,0.2)',
                  borderRadius: '12px',
                  color: '#f0f0f5',
                  fontSize: '12px',
                }}
                labelFormatter={(v) => `Jornada ${v}`}
              />
              <Line type="monotone" dataKey="cumulative" stroke="#d4a853" strokeWidth={2.5} dot={{ fill: '#d4a853', r: 4, stroke: '#12121a', strokeWidth: 2 }} activeDot={{ r: 6, fill: '#f59e0b' }} name="Puntos Acumulados" />
              <Line type="monotone" dataKey="points" stroke="#3b82f6" strokeWidth={1.5} strokeDasharray="5 5" dot={{ fill: '#3b82f6', r: 3 }} name="Puntos por Jornada" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Add Prediction Form */}
      {showForm && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="rounded-2xl border border-accent-gold/15 bg-bg-secondary/60 backdrop-blur-xl p-6 overflow-hidden"
        >
          <h2 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
            <Plus className="w-5 h-5 text-accent-gold" />
            Nueva Predicción
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">Partido</label>
                <select
                  value={formMatchId}
                  onChange={e => setFormMatchId(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-bg-tertiary/50 border border-accent-gold/10 text-text-primary text-sm focus:outline-none focus:border-accent-gold/30 appearance-none"
                  required
                >
                  <option value="" className="bg-bg-secondary">Seleccionar partido...</option>
                  {scheduledMatches.map(m => (
                    <option key={m.id} value={m.id} className="bg-bg-secondary">
                      {m.home_flag} {m.home_team_name} vs {m.away_team_name} {m.away_flag} — {m.date}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1.5">Goles Local</label>
                  <input
                    type="number"
                    min="0"
                    max="20"
                    value={formHome}
                    onChange={e => setFormHome(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl bg-bg-tertiary/50 border border-accent-gold/10 text-text-primary text-sm text-center focus:outline-none focus:border-accent-gold/30"
                    placeholder="0"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1.5">Goles Visitante</label>
                  <input
                    type="number"
                    min="0"
                    max="20"
                    value={formAway}
                    onChange={e => setFormAway(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl bg-bg-tertiary/50 border border-accent-gold/10 text-text-primary text-sm text-center focus:outline-none focus:border-accent-gold/30"
                    placeholder="0"
                    required
                  />
                </div>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">Notas (opcional)</label>
              <textarea
                value={formNotes}
                onChange={e => setFormNotes(e.target.value)}
                rows={2}
                className="w-full px-4 py-2.5 rounded-xl bg-bg-tertiary/50 border border-accent-gold/10 text-text-primary text-sm focus:outline-none focus:border-accent-gold/30 resize-none"
                placeholder="¿Por qué crees que ganará este equipo?"
              />
            </div>
            <div className="flex items-center gap-3 justify-end">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 rounded-xl text-sm text-text-secondary hover:text-text-primary transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-accent-gold to-accent-amber text-bg-primary text-sm font-semibold hover:shadow-[0_0_20px_rgba(212,168,83,0.3)] transition-shadow"
              >
                Guardar Predicción
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Pending Predictions */}
      {pendingPredictions.length > 0 && (
        <motion.div variants={item} initial="hidden" animate="show" className="rounded-2xl border border-accent-amber/15 bg-bg-secondary/60 backdrop-blur-xl p-6">
          <h2 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-accent-amber" />
            Predicciones Pendientes
            <span className="text-xs bg-accent-amber/15 text-accent-amber px-2 py-0.5 rounded-full">{pendingPredictions.length}</span>
          </h2>
          <div className="space-y-2">
            {pendingPredictions.map((pred, idx) => (
              <motion.div
                key={pred.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center justify-between p-3 rounded-xl bg-bg-tertiary/30 hover:bg-bg-tertiary/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg">{pred.home_flag}</span>
                  <span className="text-sm font-medium text-text-primary">{pred.home_team_name}</span>
                  <span className="text-sm font-bold text-accent-gold">{pred.predicted_home} - {pred.predicted_away}</span>
                  <span className="text-sm font-medium text-text-primary">{pred.away_team_name}</span>
                  <span className="text-lg">{pred.away_flag}</span>
                </div>
                <PointsBadge points={pred.points} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Predictions Table */}
      <motion.div variants={item} initial="hidden" animate="show" className="rounded-2xl border border-accent-gold/10 bg-bg-secondary/60 backdrop-blur-xl overflow-hidden">
        <div className="p-5 border-b border-accent-gold/10">
          <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-success" />
            Historial de Predicciones
          </h2>
        </div>

        {/* Desktop Table */}
        <div className="hidden sm:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left py-3 px-5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Partido</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider">Mi Predicción</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider">Resultado</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider">Puntos</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {resolvedPredictions.map((pred, idx) => (
                <motion.tr
                  key={pred.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.4 + idx * 0.04 }}
                  className="hover:bg-bg-tertiary/20 transition-colors"
                >
                  <td className="py-3 px-5">
                    <div className="flex items-center gap-2">
                      <span>{pred.home_flag}</span>
                      <span className="text-sm text-text-primary font-medium">{pred.home_team_name}</span>
                      <span className="text-xs text-text-secondary">vs</span>
                      <span className="text-sm text-text-primary font-medium">{pred.away_team_name}</span>
                      <span>{pred.away_flag}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-sm font-bold text-accent-gold">{pred.predicted_home} - {pred.predicted_away}</span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-sm font-bold text-text-primary">
                      {pred.actual_home !== null ? `${pred.actual_home} - ${pred.actual_away}` : 'Pendiente'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <PointsBadge points={pred.points} />
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Mobile Cards */}
        <div className="sm:hidden p-4 space-y-3">
          {resolvedPredictions.map((pred) => (
            <div key={pred.id} className="p-3 rounded-xl bg-bg-tertiary/30 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-sm">
                  <span>{pred.home_flag}</span>
                  <span className="font-medium text-text-primary">{pred.home_team_name}</span>
                  <span className="text-text-secondary text-xs">vs</span>
                  <span className="font-medium text-text-primary">{pred.away_team_name}</span>
                  <span>{pred.away_flag}</span>
                </div>
                <PointsBadge points={pred.points} />
              </div>
              <div className="flex items-center gap-4 text-xs">
                <span className="text-text-secondary">Predicción: <span className="text-accent-gold font-bold">{pred.predicted_home}-{pred.predicted_away}</span></span>
                <span className="text-text-secondary">Resultado: <span className="text-text-primary font-bold">{pred.actual_home !== null ? `${pred.actual_home}-${pred.actual_away}` : '-'}</span></span>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
