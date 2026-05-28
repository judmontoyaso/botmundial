'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { MapPin, Clock } from 'lucide-react';
import type { Match } from '@/types';
import FlagImg from '@/components/ui/FlagImg';

interface MatchCardProps {
  match: Match;
  compact?: boolean;
  onClick?: () => void;
  delay?: number;
}

function StatusBadge({ status }: { status: Match['status'] }) {
  const cfg: Record<string, { label: string; cls: string; dot: string }> = {
    scheduled: { label: 'Programado', cls: 'bg-info/10 text-info border-info/20',           dot: 'bg-info' },
    live:       { label: 'EN VIVO',    cls: 'badge-live text-red-400',                       dot: 'bg-red-400 animate-pulse' },
    finished:   { label: 'Finalizado', cls: 'bg-success/10 text-success border-success/20',  dot: 'bg-success' },
    completed:  { label: 'Finalizado', cls: 'bg-success/10 text-success border-success/20',  dot: 'bg-success' },
    postponed:  { label: 'Aplazado',   cls: 'bg-accent-amber/10 text-accent-amber border-accent-amber/20', dot: 'bg-accent-amber' },
  };
  const c = cfg[status] ?? cfg.scheduled;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold border ${c.cls}`}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${c.dot}`} />
      {c.label}
    </span>
  );
}

export default function MatchCard({ match, compact = false, onClick, delay = 0 }: MatchCardProps) {
  const isFinished = match.status === 'finished' || (match as any).status === 'completed';
  const isLive     = match.status === 'live';

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: 'easeOut' as const }}
      whileHover={{ y: -3, transition: { duration: 0.18 } }}
      onClick={onClick}
      className={`relative overflow-hidden rounded-2xl transition-all duration-300 ${onClick ? 'cursor-pointer' : ''} ${compact ? 'p-4' : 'p-5'}`}
      style={{
        background: isLive
          ? 'linear-gradient(135deg, rgba(239,68,68,0.08) 0%, rgba(15,15,26,0.9) 60%)'
          : 'linear-gradient(135deg, rgba(15,15,26,0.92) 0%, rgba(18,16,30,0.88) 100%)',
        border: isLive
          ? '1px solid rgba(239,68,68,0.25)'
          : '1px solid rgba(224,180,74,0.09)',
        boxShadow: isLive
          ? '0 4px 24px rgba(239,68,68,0.12), 0 0 0 1px rgba(255,255,255,0.02) inset'
          : '0 4px 20px rgba(0,0,0,0.2), 0 0 0 1px rgba(255,255,255,0.02) inset',
      }}
    >
      {/* Top highlight */}
      <div
        className="absolute top-0 left-[20%] right-[20%] h-px"
        style={{
          background: isLive
            ? 'linear-gradient(90deg, transparent, rgba(239,68,68,0.4), transparent)'
            : 'linear-gradient(90deg, transparent, rgba(224,180,74,0.2), transparent)',
        }}
      />

      {/* Hover glow overlay */}
      <div className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(224,180,74,0.04), transparent 70%)' }}
      />

      <div className="relative">
        {/* Top row */}
        <div className="flex items-center justify-between mb-4">
          {match.group ? (
            <span className="text-[10px] font-bold text-accent-gold/70 uppercase tracking-[0.1em] bg-accent-gold/8 px-2 py-0.5 rounded-md border border-accent-gold/15">
              Grupo {match.group}
            </span>
          ) : (
            <span className="text-[10px] text-text-muted uppercase tracking-wider">{match.stage}</span>
          )}
          <StatusBadge status={match.status} />
        </div>

        {/* Teams + Score */}
        <div className="flex items-center gap-2">
          {/* Home */}
          <div className="flex-1 flex flex-col items-center gap-2 min-w-0">
            <div className="p-1.5 rounded-xl bg-white/[0.04] border border-white/[0.04]">
              <FlagImg
                url={(match as any).home_flag_url}
                emoji={match.home_flag}
                teamCode={match.home_team}
                name={match.home_team_name}
                size={compact ? 'sm' : 'md'}
              />
            </div>
            <p className={`font-semibold text-text-primary text-center leading-tight ${compact ? 'text-[11px]' : 'text-xs'}`}>
              {match.home_team_name}
            </p>
          </div>

          {/* Score / VS */}
          <div className="flex-shrink-0 flex flex-col items-center gap-1 px-2">
            {isFinished ? (
              <>
                <div className="flex items-center gap-2.5">
                  <span className="text-3xl font-black text-text-primary stat-value" style={{ letterSpacing: '-0.04em' }}>
                    {match.home_score}
                  </span>
                  <span className="text-text-muted text-lg font-light">–</span>
                  <span className="text-3xl font-black text-text-primary stat-value" style={{ letterSpacing: '-0.04em' }}>
                    {match.away_score}
                  </span>
                </div>
                <span className="text-[9px] text-text-muted uppercase tracking-widest">Final</span>
              </>
            ) : isLive ? (
              <>
                <span className="text-xl font-black text-red-400 animate-pulse stat-value">EN VIVO</span>
              </>
            ) : (
              <>
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-accent-gold"
                  style={{
                    background: 'linear-gradient(135deg, rgba(224,180,74,0.12), rgba(224,180,74,0.06))',
                    border: '1px solid rgba(224,180,74,0.2)',
                  }}
                >
                  vs
                </div>
              </>
            )}
          </div>

          {/* Away */}
          <div className="flex-1 flex flex-col items-center gap-2 min-w-0">
            <div className="p-1.5 rounded-xl bg-white/[0.04] border border-white/[0.04]">
              <FlagImg
                url={(match as any).away_flag_url}
                emoji={match.away_flag}
                teamCode={match.away_team}
                name={match.away_team_name}
                size={compact ? 'sm' : 'md'}
              />
            </div>
            <p className={`font-semibold text-text-primary text-center leading-tight ${compact ? 'text-[11px]' : 'text-xs'}`}>
              {match.away_team_name}
            </p>
          </div>
        </div>

        {/* Bottom info */}
        {!compact && (
          <div
            className="flex items-center justify-center gap-4 mt-4 pt-3 text-[10px] text-text-muted"
            style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
          >
            <span className="flex items-center gap-1.5">
              <Clock className="w-3 h-3 text-text-muted/60" />
              {match.date} · {match.time}
            </span>
            <span className="w-px h-3 bg-white/[0.08]" />
            <span className="flex items-center gap-1.5">
              <MapPin className="w-3 h-3 text-text-muted/60" />
              {match.city}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
