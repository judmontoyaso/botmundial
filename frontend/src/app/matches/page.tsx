'use client';

import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Search, Filter } from 'lucide-react';
import MatchCard from '@/components/ui/MatchCard';
import { api } from '@/lib/api';
import type { Match } from '@/types';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
};

type FilterTab = 'all' | 'group' | 'knockout';

export default function MatchesPage() {
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    async function loadMatches() {
      try {
        const data = await api.getMatches();
        // El backend retorna MatchWithTeams, lo aplanamos para que coincida con el frontend Match type
        const formattedMatches = (data as any[]).map(item => ({
          ...item.match,
          home_team_name: item.home_team_name,
          away_team_name: item.away_team_name,
          home_flag: item.home_team_flag,
          away_flag: item.away_team_flag,
          date: item.match.match_date ? item.match.match_date.substring(0, 10) : '',
          time: item.match.match_date ? item.match.match_date.substring(11, 16) : '',
          group: item.match.group_letter,
        }));
        setMatches(formattedMatches);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadMatches();
  }, []);

  const filteredMatches = useMemo(() => {
    let mList = matches;

    if (activeTab === 'group') {
      mList = mList.filter(m => m.stage === 'group');
    } else if (activeTab === 'knockout') {
      mList = mList.filter(m => m.stage !== 'group');
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      mList = mList.filter(
        m =>
          m.home_team_name.toLowerCase().includes(q) ||
          m.away_team_name.toLowerCase().includes(q) ||
          m.city.toLowerCase().includes(q) ||
          m.venue.toLowerCase().includes(q)
      );
    }

    return mList.sort((a, b) => {
      if (a.status === 'scheduled' && b.status !== 'scheduled') return -1;
      if (a.status !== 'scheduled' && b.status === 'scheduled') return 1;
      return new Date(a.date).getTime() - new Date(b.date).getTime();
    });
  }, [activeTab, searchQuery, matches]);

  const tabs: { id: FilterTab; label: string }[] = [
    { id: 'all', label: 'Todos' },
    { id: 'group', label: 'Fase de Grupos' },
    { id: 'knockout', label: 'Eliminatorias' },
  ];

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
            <Calendar className="w-6 h-6 text-accent-gold" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-text-primary">
              <span className="gradient-gold-text">Partidos</span>
            </h1>
            <p className="text-text-secondary text-sm">{loading ? 'Cargando...' : `${matches.length} partidos registrados`}</p>
          </div>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
          <input
            type="text"
            placeholder="Buscar equipo, ciudad o estadio..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-bg-secondary/60 backdrop-blur-sm border border-accent-gold/10 text-text-primary text-sm placeholder:text-text-secondary/50 focus:outline-none focus:border-accent-gold/30 focus:shadow-[0_0_15px_rgba(212,168,83,0.08)] transition-all"
          />
        </div>
      </motion.div>

      {/* Filter Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex items-center gap-2"
      >
        <Filter className="w-4 h-4 text-text-secondary" />
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
              activeTab === tab.id
                ? 'bg-accent-gold/15 text-accent-gold border border-accent-gold/20 shadow-[0_0_12px_rgba(212,168,83,0.1)]'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50 border border-transparent'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </motion.div>

      {/* Results count */}
      <p className="text-xs text-text-secondary">
        {loading ? 'Sincronizando datos...' : `Mostrando ${filteredMatches.length} partido${filteredMatches.length !== 1 ? 's' : ''}`}
      </p>

      {/* Matches Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-gold"></div>
        </div>
      ) : filteredMatches.length > 0 ? (
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          key={`${activeTab}-${searchQuery}`}
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
        >
          {filteredMatches.map((match, idx) => (
            <MatchCard key={match.id} match={match} delay={idx * 0.04} />
          ))}
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <Calendar className="w-12 h-12 text-text-secondary/30 mx-auto mb-4" />
          <p className="text-text-secondary">No se encontraron partidos</p>
          <p className="text-text-secondary/60 text-sm mt-1">Intenta con otra búsqueda</p>
        </motion.div>
      )}
    </div>
  );
}
