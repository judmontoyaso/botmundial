'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface ProbabilityBarProps {
  homeWin: number;
  draw: number;
  awayWin: number;
  homeTeam: string;
  awayTeam: string;
}

export default function ProbabilityBar({ homeWin, draw, awayWin, homeTeam, awayTeam }: ProbabilityBarProps) {
  const homePercent = Math.round(homeWin * 100);
  const drawPercent = Math.round(draw * 100);
  const awayPercent = Math.round(awayWin * 100);

  return (
    <div className="w-full">
      {/* Team labels */}
      <div className="flex justify-between text-xs font-medium mb-2">
        <span className="text-success">{homeTeam}</span>
        <span className="text-text-secondary">Empate</span>
        <span className="text-info">{awayTeam}</span>
      </div>

      {/* Bar */}
      <div className="flex h-3 rounded-full overflow-hidden bg-bg-tertiary/50 gap-0.5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${homePercent}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
          className="bg-gradient-to-r from-success to-emerald-400 rounded-l-full"
        />
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${drawPercent}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.4 }}
          className="bg-gradient-to-r from-text-secondary/60 to-text-secondary/40"
        />
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${awayPercent}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.6 }}
          className="bg-gradient-to-r from-blue-500 to-info rounded-r-full"
        />
      </div>

      {/* Percentages */}
      <div className="flex justify-between text-xs mt-1.5">
        <span className="text-success font-semibold">{homePercent}%</span>
        <span className="text-text-secondary font-semibold">{drawPercent}%</span>
        <span className="text-info font-semibold">{awayPercent}%</span>
      </div>
    </div>
  );
}
