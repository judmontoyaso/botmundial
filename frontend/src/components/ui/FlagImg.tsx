'use client';

import React, { useState } from 'react';
import { getFlagEmoji } from '@/lib/flags';

interface FlagImgProps {
  url?: string;
  emoji?: string;
  teamCode?: string;
  name: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap = {
  sm: { img: 'w-7 h-5', emoji: 'text-2xl' },
  md: { img: 'w-9 h-6', emoji: 'text-3xl' },
  lg: { img: 'w-12 h-8', emoji: 'text-4xl' },
};

export default function FlagImg({ url, emoji, teamCode, name, size = 'md' }: FlagImgProps) {
  const [imgFailed, setImgFailed] = useState(false);
  const { img, emoji: emojiClass } = sizeMap[size];

  if (url && !imgFailed) {
    return (
      <img
        src={url}
        alt={name}
        className={`${img} object-cover rounded-sm shadow-sm flex-shrink-0`}
        onError={() => setImgFailed(true)}
      />
    );
  }

  const flagChar = emoji || (teamCode ? getFlagEmoji(teamCode) : '🏳️');
  return <span className={`${emojiClass} flex-shrink-0 leading-none`}>{flagChar}</span>;
}
