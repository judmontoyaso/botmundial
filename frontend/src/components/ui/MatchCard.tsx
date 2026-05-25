'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { MapPin, Clock } from 'lucide-react';
import type { Match } from '@/types';

interface MatchCardProps {
  match: Match;
  compact?: boolean;
  onClick?: () => void;
  delay?: number;
}

function StatusBadge({ status }: { status: Match['status'] }) {
  const config = {
    scheduled: { label: 'Programado', bg: 'bg-info/15', text: 'text-info', dot: 'bg-info' },
    live: { label: 'EN VIVO', bg: 'bg-danger/15', text: 'text-danger', dot: 'bg-danger animate-pulse' },
    finished: { label: 'Finalizado', bg: 'bg-success/15', text: 'text-success', dot: 'bg-success' },
    postponed: { label: 'Aplazado', bg: 'bg-accent-amber/15', text: 'text-accent-amber', dot: 'bg-accent-amber' },
  };
  const c = config[status];

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}

export default function MatchCard({ match, compact = false, onClick, delay = 0 }: MatchCardProps) {
  const isFinished = match.status === 'finished';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      onClick={onClick}
      className={`relative overflow-hidden rounded-2xl border border-accent-gold/10 bg-bg-secondary/60 backdrop-blur-xl transition-all duration-300 hover:border-accent-gold/25 hover:shadow-[0_0_25px_rgba(212,168,83,0.08)] ${onClick ? 'cursor-pointer' : ''} ${compact ? 'p-4' : 'p-5'}`}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none" />

      <div className="relative">
        {/* Top row: group + status */}
        <div className="flex items-center justify-between mb-3">
          {match.group && (
            <span className="text-xs font-semibold text-accent-gold/80 uppercase tracking-wider">
              Grupo {match.group}
            </span>
          )}
          <StatusBadge status={match.status} />
        </div>

        {/* Teams and Score */}
        <div className="flex items-center justify-between gap-3">
          {/* Home team */}
          <div className="flex-1 text-center">
            <div className={`${compact ? 'text-2xl' : 'text-3xl'} mb-1`}>{match.home_flag}</div>
            <p className={`font-semibold text-text-primary ${compact ? 'text-xs' : 'text-sm'} leading-tight`}>
              {match.home_team_name}
            </p>
          </div>

          {/* Score / VS */}
          <div className="flex-shrink-0 px-3">
            {isFinished ? (
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-text-primary">{match.home_score}</span>
                <span className="text-text-secondary text-lg">-</span>
                <span className="text-2xl font-bold text-text-primary">{match.away_score}</span>
              </div>
            ) : (
              <span className="text-xl font-bold text-accent-gold">vs</span>
            )}
          </div>

          {/* Away team */}
          <div className="flex-1 text-center">
            <div className={`${compact ? 'text-2xl' : 'text-3xl'} mb-1`}>{match.away_flag}</div>
            <p className={`font-semibold text-text-primary ${compact ? 'text-xs' : 'text-sm'} leading-tight`}>
              {match.away_team_name}
            </p>
          </div>
        </div>

        {/* Bottom info */}
        {!compact && (
          <div className="flex items-center justify-center gap-4 mt-4 text-xs text-text-secondary">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {match.date} · {match.time}
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {match.venue}, {match.city}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
