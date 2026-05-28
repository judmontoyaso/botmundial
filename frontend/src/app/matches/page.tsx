'use client';

import React, { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Search, Filter, RefreshCw, X, ChevronDown } from 'lucide-react';
import MatchCard from '@/components/ui/MatchCard';
import LoadingBall from '@/components/ui/LoadingBall';
import MatchStatsModal from '@/components/ui/MatchStatsModal';
import FlagImg from '@/components/ui/FlagImg';
import { api } from '@/lib/api';
import type { Match } from '@/types';

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.04 } },
};

type FilterTab = 'all' | 'group' | 'knockout';

interface TeamOption {
  code: string;
  name: string;
  flag: string;
  flag_url: string;
  confederation: string;
}

const CONF_ORDER = ['CONCACAF', 'CONMEBOL', 'UEFA', 'AFC', 'CAF', 'OFC'];
const CONF_LABELS: Record<string, string> = {
  CONCACAF: 'CONCACAF', CONMEBOL: 'CONMEBOL', UEFA: 'UEFA',
  AFC: 'Asia (AFC)', CAF: 'África (CAF)', OFC: 'Oceanía (OFC)',
};

// Small inline team picker dropdown
function TeamPicker({
  teams,
  selected,
  onChange,
}: {
  teams: TeamOption[];
  selected: string[];
  onChange: (codes: string[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  const grouped = useMemo(() => {
    const q = search.toLowerCase();
    const filtered = teams.filter(
      t => t.name.toLowerCase().includes(q) || t.code.toLowerCase().includes(q)
    );
    const map: Record<string, TeamOption[]> = {};
    for (const t of filtered) {
      const conf = t.confederation.toUpperCase();
      if (!map[conf]) map[conf] = [];
      map[conf].push(t);
    }
    return CONF_ORDER.map(c => ({ conf: c, label: CONF_LABELS[c] ?? c, teams: map[c] ?? [] }))
      .filter(g => g.teams.length > 0);
  }, [teams, search]);

  const toggle = (code: string) => {
    onChange(selected.includes(code) ? selected.filter(c => c !== code) : [...selected, code]);
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-all border ${
          selected.length > 0
            ? 'bg-accent-gold/15 text-accent-gold border-accent-gold/25'
            : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50 border-transparent'
        }`}
      >
        <span>País</span>
        {selected.length > 0 && (
          <span className="w-4 h-4 rounded-full bg-accent-gold text-bg-primary text-[10px] font-bold flex items-center justify-center">
            {selected.length}
          </span>
        )}
        <ChevronDown className={`w-3.5 h-3.5 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 mt-2 z-30 w-72 rounded-2xl bg-bg-secondary border border-accent-gold/15 shadow-2xl overflow-hidden"
          >
            {/* Search inside picker */}
            <div className="p-3 border-b border-accent-gold/8">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-secondary/50" />
                <input
                  autoFocus
                  type="text"
                  placeholder="Buscar selección..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-bg-tertiary/60 border border-accent-gold/10 text-text-primary text-xs placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-gold/25 transition-all"
                />
              </div>
            </div>

            {/* Team list */}
            <div className="max-h-72 overflow-y-auto p-2 space-y-3">
              {grouped.length === 0 && (
                <p className="text-center text-xs text-text-secondary/50 py-4">Sin resultados</p>
              )}
              {grouped.map(({ conf, label, teams: gTeams }) => (
                <div key={conf}>
                  <p className="text-[10px] font-semibold text-text-secondary/50 uppercase tracking-wider px-1 mb-1">{label}</p>
                  <div className="grid grid-cols-2 gap-1">
                    {gTeams.map(t => {
                      const active = selected.includes(t.code);
                      return (
                        <button
                          key={t.code}
                          onClick={() => toggle(t.code)}
                          className={`flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs transition-all text-left ${
                            active
                              ? 'bg-accent-gold/15 text-accent-gold border border-accent-gold/20'
                              : 'hover:bg-bg-tertiary/60 text-text-secondary hover:text-text-primary border border-transparent'
                          }`}
                        >
                          <FlagImg url={t.flag_url} emoji={t.flag} teamCode={t.code} name={t.name} size="sm" />
                          <span className="truncate leading-tight">{t.name}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            {/* Footer */}
            {selected.length > 0 && (
              <div className="p-2 border-t border-accent-gold/8">
                <button
                  onClick={() => { onChange([]); setOpen(false); }}
                  className="w-full text-xs text-text-secondary hover:text-danger transition-colors py-1"
                >
                  Limpiar filtro
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function MatchesPage() {
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  const loadMatches = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getMatches();
      const formattedMatches = (data as any[]).map(item => ({
        ...item.match,
        home_team: item.match.home_team_code,
        away_team: item.match.away_team_code,
        home_team_name: item.home_team_name,
        away_team_name: item.away_team_name,
        home_flag: item.home_team_flag,
        away_flag: item.away_team_flag,
        home_flag_url: item.home_team_flag_url ?? '',
        away_flag_url: item.away_team_flag_url ?? '',
        date: item.match.match_date ? item.match.match_date.substring(0, 10) : '',
        time: item.match.match_date ? item.match.match_date.substring(11, 16) : '',
        group: item.match.group_letter,
        home_confederation: item.home_team_confederation ?? '',
        away_confederation: item.away_team_confederation ?? '',
      }));
      setMatches(formattedMatches);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSync = useCallback(async () => {
    setSyncing(true);
    setSyncMsg(null);
    try {
      const result = await api.runSync();
      setSyncMsg(result.synced > 0 ? `${result.synced} resultado(s) actualizado(s)` : 'Todo al día');
      if (result.synced > 0) await loadMatches();
    } catch {
      setSyncMsg('Error al sincronizar');
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncMsg(null), 4000);
    }
  }, [loadMatches]);

  React.useEffect(() => { loadMatches(); }, [loadMatches]);

  // Build unique team list from loaded matches (preserves confederation via API)
  const teamOptions = useMemo((): TeamOption[] => {
    const map = new Map<string, TeamOption>();
    for (const m of matches) {
      if (!map.has(m.home_team)) {
        map.set(m.home_team, {
          code: m.home_team,
          name: m.home_team_name,
          flag: m.home_flag,
          flag_url: (m as any).home_flag_url ?? '',
          confederation: (m as any).home_confederation ?? '',
        });
      }
      if (!map.has(m.away_team)) {
        map.set(m.away_team, {
          code: m.away_team,
          name: m.away_team_name,
          flag: m.away_flag,
          flag_url: (m as any).away_flag_url ?? '',
          confederation: (m as any).away_confederation ?? '',
        });
      }
    }
    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [matches]);

  const filteredMatches = useMemo(() => {
    let mList = matches;

    if (activeTab === 'group') mList = mList.filter(m => m.stage === 'group');
    else if (activeTab === 'knockout') mList = mList.filter(m => m.stage !== 'group');

    if (selectedTeams.length > 0) {
      mList = mList.filter(
        m => selectedTeams.includes(m.home_team) || selectedTeams.includes(m.away_team)
      );
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
  }, [activeTab, searchQuery, selectedTeams, matches]);

  const tabs: { id: FilterTab; label: string }[] = [
    { id: 'all', label: 'Todos' },
    { id: 'group', label: 'Grupos' },
    { id: 'knockout', label: 'Eliminatorias' },
  ];

  // Selected team chips for display below filters
  const selectedTeamOptions = teamOptions.filter(t => selectedTeams.includes(t.code));

  return (
    <div className="max-w-7xl mx-auto space-y-5">
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
            <p className="text-text-secondary text-sm">
              {loading ? 'Cargando...' : `${matches.length} partidos registrados`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          {syncMsg && <span className="text-xs text-accent-gold/80">{syncMsg}</span>}
          <button
            onClick={handleSync}
            disabled={syncing}
            title="Sincronizar resultados en vivo"
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-bg-tertiary/50 border border-accent-gold/10 text-text-secondary hover:text-accent-gold hover:border-accent-gold/25 transition-all text-xs disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Sincronizar</span>
          </button>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
          <input
            type="text"
            placeholder="Buscar equipo, ciudad, estadio..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-bg-secondary/60 backdrop-blur-sm border border-accent-gold/10 text-text-primary text-sm placeholder:text-text-secondary/50 focus:outline-none focus:border-accent-gold/30 transition-all"
          />
        </div>
      </motion.div>

      {/* Filters row */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex items-center gap-2 flex-wrap"
      >
        <Filter className="w-4 h-4 text-text-secondary flex-shrink-0" />

        {/* Stage tabs */}
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

        <div className="w-px h-5 bg-accent-gold/10 mx-1" />

        {/* Country picker */}
        <TeamPicker teams={teamOptions} selected={selectedTeams} onChange={setSelectedTeams} />
      </motion.div>

      {/* Active team chips */}
      <AnimatePresence>
        {selectedTeamOptions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex flex-wrap gap-2"
          >
            {selectedTeamOptions.map(t => (
              <motion.button
                key={t.code}
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.85 }}
                onClick={() => setSelectedTeams(prev => prev.filter(c => c !== t.code))}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-accent-gold/10 border border-accent-gold/20 text-accent-gold text-xs hover:bg-danger/10 hover:border-danger/20 hover:text-danger transition-all"
              >
                <FlagImg url={t.flag_url} emoji={t.flag} teamCode={t.code} name={t.name} size="sm" />
                <span>{t.name}</span>
                <X className="w-3 h-3" />
              </motion.button>
            ))}
            <button
              onClick={() => setSelectedTeams([])}
              className="text-xs text-text-secondary/50 hover:text-text-secondary transition-colors px-1"
            >
              Limpiar todo
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results count */}
      <p className="text-xs text-text-secondary">
        {loading
          ? 'Cargando...'
          : `${filteredMatches.length} partido${filteredMatches.length !== 1 ? 's' : ''}${
              selectedTeams.length > 0 || searchQuery ? ' (filtrado)' : ''
            }`}
      </p>

      {/* Matches Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <LoadingBall text="Cargando partidos..." />
        </div>
      ) : filteredMatches.length > 0 ? (
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          key={`${activeTab}-${searchQuery}-${selectedTeams.join(',')}`}
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
        >
          {filteredMatches.map((match, idx) => (
            <MatchCard
              key={match.id}
              match={match}
              delay={idx * 0.04}
              onClick={() => setSelectedMatch(match)}
            />
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
          <p className="text-text-secondary/60 text-sm mt-1">Intenta con otro filtro</p>
        </motion.div>
      )}

      <MatchStatsModal match={selectedMatch} onClose={() => setSelectedMatch(null)} />
    </div>
  );
}
