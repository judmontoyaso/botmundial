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
  color?: 'gold' | 'blue' | 'green' | 'red' | 'amber';
  delay?: number;
}

const colorMap = {
  gold: { bg: 'bg-accent-gold/10', text: 'text-accent-gold', border: 'border-accent-gold/20', glow: 'shadow-[0_0_20px_rgba(212,168,83,0.1)]' },
  blue: { bg: 'bg-info/10', text: 'text-info', border: 'border-info/20', glow: 'shadow-[0_0_20px_rgba(59,130,246,0.1)]' },
  green: { bg: 'bg-success/10', text: 'text-success', border: 'border-success/20', glow: 'shadow-[0_0_20px_rgba(34,197,94,0.1)]' },
  red: { bg: 'bg-danger/10', text: 'text-danger', border: 'border-danger/20', glow: 'shadow-[0_0_20px_rgba(239,68,68,0.1)]' },
  amber: { bg: 'bg-accent-amber/10', text: 'text-accent-amber', border: 'border-accent-amber/20', glow: 'shadow-[0_0_20px_rgba(245,158,11,0.1)]' },
};

export default function StatsCard({ icon: Icon, label, value, trend, color = 'gold', delay = 0 }: StatsCardProps) {
  const colors = colorMap[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className={`relative overflow-hidden rounded-2xl border ${colors.border} bg-bg-secondary/60 backdrop-blur-xl p-6 ${colors.glow} transition-shadow duration-300 hover:shadow-[0_0_30px_rgba(212,168,83,0.15)]`}
    >
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none" />

      <div className="relative flex items-start justify-between">
        <div className="flex-1">
          <p className="text-text-secondary text-sm font-medium mb-1">{label}</p>
          <p className="text-3xl font-bold text-text-primary tracking-tight">{value}</p>
          {trend && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${trend.positive ? 'text-success' : 'text-danger'}`}>
              {trend.positive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span className="font-medium">{trend.positive ? '+' : ''}{trend.value}%</span>
            </div>
          )}
        </div>
        <div className={`${colors.bg} rounded-xl p-3`}>
          <Icon className={`w-6 h-6 ${colors.text}`} />
        </div>
      </div>
    </motion.div>
  );
}
