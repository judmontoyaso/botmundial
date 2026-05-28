'use client';

import React from 'react';

interface LoadingBallProps {
  text?: string;
  size?: number;
}

export default function LoadingBall({ text = 'Cargando...', size = 64 }: LoadingBallProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/logo.png"
        alt="Cargando"
        width={size}
        height={size}
        className="animate-spin"
        style={{ animationDuration: '1.5s' }}
      />
      {text && (
        <p className="text-text-secondary font-medium animate-pulse text-sm">{text}</p>
      )}
    </div>
  );
}
