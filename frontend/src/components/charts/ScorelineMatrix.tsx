'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface ScorelineMatrixProps {
  matrix: number[][];
  homeTeam: string;
  awayTeam: string;
  predictedHome: number;
  predictedAway: number;
}

export default function ScorelineMatrix({
  matrix,
  homeTeam,
  awayTeam,
  predictedHome,
  predictedAway,
}: ScorelineMatrixProps) {
  if (!matrix || matrix.length === 0) return null;

  const maxGoals = matrix.length - 1;

  const maxProb = Math.max(...matrix.flat());

  function getColor(prob: number, h: number, a: number): string {
    const intensity = maxProb > 0 ? prob / maxProb : 0;
    // Most likely scoreline → gold highlight
    if (h === predictedHome && a === predictedAway) {
      return `rgba(212,168,83,${0.3 + intensity * 0.7})`;
    }
    // Home wins → green tint
    if (h > a) return `rgba(34,197,94,${intensity * 0.65})`;
    // Away wins → blue tint
    if (a > h) return `rgba(59,130,246,${intensity * 0.65})`;
    // Draw → grey
    return `rgba(136,136,160,${intensity * 0.65})`;
  }

  function formatPct(p: number): string {
    const pct = p * 100;
    if (pct < 0.5) return '<1%';
    return `${Math.round(pct)}%`;
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-accent-gold uppercase tracking-wider">
          Matriz de Marcadores (Poisson)
        </span>
        <div className="flex items-center gap-3 text-[10px] text-text-secondary">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm inline-block bg-success/50" />
            Local gana
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ background: 'rgba(136,136,160,0.5)' }} />
            Empate
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm inline-block bg-info/50" />
            Visitante gana
          </span>
        </div>
      </div>

      <div className="overflow-auto">
        <table className="w-full text-center border-collapse">
          <thead>
            <tr>
              <th className="text-[10px] text-text-secondary font-normal pb-1 pr-1 text-right w-10">
                <span className="text-[9px]">Local ↓ / Vis →</span>
              </th>
              {Array.from({ length: maxGoals + 1 }, (_, a) => (
                <th key={a} className="text-[10px] text-text-secondary font-semibold pb-1 px-0.5 w-10">
                  {a}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, h) => (
              <tr key={h}>
                <td className="text-[10px] text-text-secondary font-semibold pr-1 text-right">
                  {h}
                </td>
                {row.map((prob, a) => {
                  const isMostLikely = h === predictedHome && a === predictedAway;
                  return (
                    <motion.td
                      key={a}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: (h * (maxGoals + 1) + a) * 0.012 }}
                      className={`text-[10px] font-medium px-0.5 py-0.5 rounded transition-all ${
                        isMostLikely
                          ? 'ring-1 ring-accent-gold text-accent-gold font-bold'
                          : 'text-text-secondary'
                      }`}
                      style={{
                        background: getColor(prob, h, a),
                        minWidth: '2.2rem',
                        height: '2.2rem',
                      }}
                      title={`${homeTeam} ${h}-${a} ${awayTeam}: ${(prob * 100).toFixed(1)}%`}
                    >
                      {formatPct(prob)}
                    </motion.td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Axis labels */}
      <div className="flex justify-between mt-2 text-[10px] text-text-secondary/70">
        <span>← {homeTeam} (goles local)</span>
        <span>{awayTeam} (goles visitante) →</span>
      </div>
    </div>
  );
}
