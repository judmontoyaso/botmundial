'use client';

import React from 'react';
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatsCardProps {
  icon: LucideIcon;
  label: string;
  value: React.ReactNode;
  trend?: { value: number; positive: boolean };
  color?: 'gold' | 'blue' | 'green' | 'red' | 'amber' | 'purple';
  delay?: number;
}

const colorMap = {
  gold:   { icon: 'text-accent-gold',   iconBg: 'bg-accent-gold/10',   ring: 'rgba(224,180,74,0.18)',  glow: 'rgba(224,180,74,0.08)',  bar: '#e0b44a' },
  blue:   { icon: 'text-info',          iconBg: 'bg-info/10',          ring: 'rgba(59,130,246,0.18)',  glow: 'rgba(59,130,246,0.08)',  bar: '#3b82f6' },
  green:  { icon: 'text-success',       iconBg: 'bg-success/10',       ring: 'rgba(34,197,94,0.18)',   glow: 'rgba(34,197,94,0.08)',   bar: '#22c55e' },
  red:    { icon: 'text-danger',        iconBg: 'bg-danger/10',        ring: 'rgba(239,68,68,0.18)',   glow: 'rgba(239,68,68,0.08)',   bar: '#ef4444' },
  amber:  { icon: 'text-accent-amber',  iconBg: 'bg-accent-amber/10',  ring: 'rgba(245,158,11,0.18)',  glow: 'rgba(245,158,11,0.08)',  bar: '#f59e0b' },
  purple: { icon: 'text-accent-purple', iconBg: 'bg-accent-purple/10', ring: 'rgba(139,92,246,0.18)',  glow: 'rgba(139,92,246,0.08)',  bar: '#8b5cf6' },
};

export default function StatsCard({ icon: Icon, label, value, trend, color = 'gold', delay = 0 }: StatsCardProps) {
  const c = colorMap[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay, ease: 'easeOut' as const }}
      whileHover={{ y: -4, transition: { duration: 0.18 } }}
      className="relative overflow-hidden rounded-2xl"
      style={{
        background: 'linear-gradient(135deg, rgba(15,15,26,0.9) 0%, rgba(18,16,32,0.85) 100%)',
        border: `1px solid ${c.ring}`,
        boxShadow: `0 4px 24px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.03) inset`,
      }}
    >
      {/* Top highlight line */}
      <div
        className="absolute top-0 left-[15%] right-[15%] h-px"
        style={{ background: `linear-gradient(90deg, transparent, ${c.bar}55, transparent)` }}
      />

      {/* Background watermark icon */}
      <div className="absolute -right-3 -bottom-3 opacity-[0.04]">
        <Icon style={{ width: 80, height: 80, color: c.bar }} />
      </div>

      <div className="relative p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <p className="text-text-secondary text-xs font-medium uppercase tracking-wider mb-2">{label}</p>
            <p
              className="text-4xl font-bold text-text-primary leading-none mb-1 stat-value animate-count-up"
              style={{ letterSpacing: '-0.03em' }}
            >
              {value}
            </p>
            {trend && (
              <div className={`flex items-center gap-1 mt-2 text-xs font-semibold ${trend.positive ? 'text-success' : 'text-danger'}`}>
                {trend.positive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                <span>{trend.positive ? '+' : ''}{trend.value}%</span>
                <span className="text-text-muted font-normal">vs. mes anterior</span>
              </div>
            )}
          </div>
          <div className={`${c.iconBg} rounded-xl p-3 flex-shrink-0`} style={{ boxShadow: `0 0 16px ${c.glow}` }}>
            <Icon className={`w-5 h-5 ${c.icon}`} />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
