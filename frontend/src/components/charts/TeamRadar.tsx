'use client';

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';

interface TeamRadarProps {
  teamA: {
    name: string;
    stats: {
      attack: number;
      defense: number;
      midfield: number;
      form: number;
      experience: number;
      homeAdvantage: number;
    };
  };
  teamB: {
    name: string;
    stats: {
      attack: number;
      defense: number;
      midfield: number;
      form: number;
      experience: number;
      homeAdvantage: number;
    };
  };
}

export default function TeamRadar({ teamA, teamB }: TeamRadarProps) {
  const data = [
    {
      subject: 'Ataque',
      A: teamA.stats.attack,
      B: teamB.stats.attack,
      fullMark: 100,
    },
    {
      subject: 'Defensa',
      A: teamA.stats.defense,
      B: teamB.stats.defense,
      fullMark: 100,
    },
    {
      subject: 'Mediocampo',
      A: teamA.stats.midfield,
      B: teamB.stats.midfield,
      fullMark: 100,
    },
    {
      subject: 'Forma',
      A: teamA.stats.form,
      B: teamB.stats.form,
      fullMark: 100,
    },
    {
      subject: 'Experiencia',
      A: teamA.stats.experience,
      B: teamB.stats.experience,
      fullMark: 100,
    },
    {
      subject: 'Localía',
      A: teamA.stats.homeAdvantage,
      B: teamB.stats.homeAdvantage,
      fullMark: 100,
    },
  ];

  return (
    <div className="w-full h-full min-h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#333344" />
          <PolarAngleAxis 
            dataKey="subject" 
            tick={{ fill: '#8888a0', fontSize: 12 }} 
          />
          <PolarRadiusAxis 
            angle={30} 
            domain={[0, 100]} 
            tick={false} 
            axisLine={false} 
          />
          <Radar
            name={teamA.name}
            dataKey="A"
            stroke="#d4a853"
            fill="#d4a853"
            fillOpacity={0.5}
          />
          <Radar
            name={teamB.name}
            dataKey="B"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.5}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#12121a', 
              borderColor: '#333344',
              borderRadius: '8px',
              color: '#f0f0f5'
            }}
            itemStyle={{ color: '#f0f0f5' }}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
