'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Calendar,
  Brain,
  Users,
  Target,
  Menu,
  X,
  Trophy,
  GitBranch,
  Zap,
  FlaskConical,
} from 'lucide-react';

const navItems = [
  { href: '/',           label: 'Dashboard',       icon: LayoutDashboard, desc: 'Resumen general' },
  { href: '/matches',    label: 'Partidos',         icon: Calendar,        desc: 'Programación' },
  { href: '/predictions',label: 'Predicciones IA',  icon: Brain,           desc: 'Modelo Poisson' },
  { href: '/groups',     label: 'Grupos',           icon: Users,           desc: 'Fase de grupos' },
  { href: '/bracket',    label: 'Simulación',       icon: GitBranch,       desc: 'Monte Carlo' },
  { href: '/tracker',    label: 'Mi Polla',         icon: Target,          desc: 'Mis apuestas' },
  { href: '/backtest',   label: 'Backtest',          icon: FlaskConical,    desc: 'Qatar 2022' },
];

function Countdown() {
  const [t, setT] = useState({ d: 0, h: 0, m: 0 });
  useEffect(() => {
    const target = new Date('2026-06-11T18:00:00Z');
    const tick = () => {
      const diff = target.getTime() - Date.now();
      if (diff > 0) setT({
        d: Math.floor(diff / 86400000),
        h: Math.floor((diff % 86400000) / 3600000),
        m: Math.floor((diff % 3600000) / 60000),
      });
    };
    tick();
    const id = setInterval(tick, 60000);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="flex items-center justify-center gap-2 mt-2">
      {[{ val: t.d, lbl: 'días' }, { val: t.h, lbl: 'hrs' }, { val: t.m, lbl: 'min' }].map(({ val, lbl }) => (
        <div key={lbl} className="flex flex-col items-center">
          <span className="text-base font-bold text-accent-gold tabular-nums leading-none stat-value">{String(val).padStart(2,'0')}</span>
          <span className="text-[9px] text-text-muted uppercase tracking-wider">{lbl}</span>
        </div>
      ))}
    </div>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href);

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="px-5 pt-6 pb-5">
        <Link href="/" onClick={() => setMobileOpen(false)} className="flex items-center gap-3 group">
          <div className="relative flex-shrink-0">
            <div className="absolute inset-0 rounded-2xl bg-accent-gold/20 blur-lg group-hover:bg-accent-gold/35 transition-all duration-500" />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/logo.png"
              alt="ProMundial"
              width={48}
              height={48}
              className="relative w-12 h-12 object-contain drop-shadow-[0_0_10px_rgba(224,180,74,0.6)] group-hover:drop-shadow-[0_0_18px_rgba(224,180,74,0.9)] group-hover:scale-105 transition-all duration-300"
            />
          </div>
          <div>
            <h1 className="text-xl font-extrabold gradient-gold-text leading-tight tracking-tight">ProMundial</h1>
            <p className="text-[10px] text-text-muted tracking-widest uppercase mt-0.5 flex items-center gap-1">
              <Zap className="w-2.5 h-2.5 text-accent-gold/70" />
              IA · FIFA 2026
            </p>
          </div>
        </Link>
      </div>

      {/* Divider */}
      <div className="mx-4 mb-4 h-px bg-gradient-to-r from-transparent via-accent-gold/15 to-transparent" />

      {/* Nav */}
      <nav className="flex-1 px-3 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              onClick={() => setMobileOpen(false)}
              className={`relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group overflow-hidden ${
                active
                  ? 'text-accent-gold'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              {/* Active background */}
              {active && (
                <motion.div
                  layoutId="nav-active-bg"
                  className="absolute inset-0 rounded-xl"
                  style={{
                    background: 'linear-gradient(135deg, rgba(224,180,74,0.12) 0%, rgba(224,180,74,0.06) 100%)',
                  }}
                  transition={{ type: 'spring', stiffness: 400, damping: 35 }}
                />
              )}
              {/* Hover background */}
              {!active && (
                <div className="absolute inset-0 rounded-xl bg-bg-tertiary/0 group-hover:bg-bg-tertiary/50 transition-colors duration-200" />
              )}
              {/* Left accent bar */}
              {active && (
                <motion.div
                  layoutId="nav-active-bar"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r-full"
                  style={{ background: 'linear-gradient(180deg, #f0c060, #e0b44a)' }}
                  transition={{ type: 'spring', stiffness: 400, damping: 35 }}
                />
              )}
              <Icon className={`w-[18px] h-[18px] relative z-10 flex-shrink-0 transition-all duration-200 ${
                active ? 'text-accent-gold' : 'text-text-muted group-hover:text-text-secondary'
              }`} />
              <span className="relative z-10 leading-none">{label}</span>
              {active && (
                <span className="relative z-10 ml-auto w-1.5 h-1.5 rounded-full bg-accent-gold/80 flex-shrink-0" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer: WC countdown */}
      <div className="px-3 pb-5 pt-3">
        <div className="mx-px h-px bg-gradient-to-r from-transparent via-accent-gold/12 to-transparent mb-4" />
        <div className="rounded-2xl overflow-hidden relative">
          <div className="absolute inset-0 bg-gradient-to-br from-accent-gold/8 via-bg-tertiary/40 to-accent-purple/5" />
          <div className="relative px-4 py-3 text-center">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Trophy className="w-3.5 h-3.5 text-accent-gold" />
              <span className="text-[11px] font-semibold text-accent-gold/90 uppercase tracking-wider">Inicio del Mundial</span>
            </div>
            <Countdown />
            <p className="text-[9px] text-text-muted mt-2 uppercase tracking-widest">11 Jun 2026 · México</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop */}
      <aside
        className="hidden lg:flex fixed left-0 top-0 z-40 h-screen flex-col border-r border-white/[0.04]"
        style={{
          width: '260px',
          background: 'linear-gradient(180deg, #0c0c18 0%, #09090f 100%)',
        }}
      >
        <SidebarContent />
      </aside>

      {/* Mobile button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2.5 rounded-xl backdrop-blur-xl border border-white/[0.06] text-text-primary"
        style={{ background: 'rgba(12,12,24,0.9)' }}
        aria-label="Abrir menú"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Mobile overlay + drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 z-40 bg-black/70 backdrop-blur-sm"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', stiffness: 320, damping: 32 }}
              className="lg:hidden fixed left-0 top-0 z-50 h-screen border-r border-white/[0.05]"
              style={{ width: '260px', background: 'linear-gradient(180deg, #0c0c18 0%, #09090f 100%)' }}
            >
              <button
                onClick={() => setMobileOpen(false)}
                className="absolute top-4 right-4 p-1.5 rounded-lg text-text-muted hover:text-text-primary transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
