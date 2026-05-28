'use client';

import React, { useState } from 'react';
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
} from 'lucide-react';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/matches', label: 'Partidos', icon: Calendar },
  { href: '/predictions', label: 'Predicciones AI', icon: Brain },
  { href: '/groups', label: 'Grupos', icon: Users },
  { href: '/tracker', label: 'Mi Polla', icon: Target },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="px-5 pt-4 pb-4 border-b border-accent-gold/10">
        <Link href="/" className="flex items-center gap-3 group" onClick={() => setMobileOpen(false)}>
          <div className="relative flex-shrink-0">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-accent-gold via-accent-amber to-yellow-600 flex items-center justify-center shadow-lg shadow-accent-gold/30 group-hover:shadow-accent-gold/50 transition-shadow duration-300">
              <Trophy className="w-6 h-6 text-bg-primary drop-shadow-sm" />
            </div>
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-accent-gold to-accent-amber opacity-0 group-hover:opacity-50 blur-xl transition-opacity duration-500" />
          </div>
          <div className="min-w-0">
            <h1 className="text-xl font-extrabold gradient-gold-text leading-tight tracking-tight">ProMundial</h1>
            <p className="text-[10px] text-text-secondary tracking-widest uppercase mt-0.5">Análisis IA · 2026</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const active = isActive(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={`relative flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group ${
                active
                  ? 'text-accent-gold bg-accent-gold/10'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50'
              }`}
            >
              {active && (
                <motion.div
                  layoutId="active-nav"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full bg-gradient-to-b from-accent-gold to-accent-amber"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
              {active && (
                <div className="absolute inset-0 rounded-xl bg-accent-gold/5 shadow-[0_0_15px_rgba(212,168,83,0.08)]" />
              )}
              <Icon className={`w-5 h-5 relative z-10 transition-colors ${active ? 'text-accent-gold' : 'group-hover:text-text-primary'}`} />
              <span className="relative z-10">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer Badge */}
      <div className="p-4 border-t border-accent-gold/10">
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-bg-tertiary/30">
          <span className="text-lg">⚽</span>
          <div>
            <p className="text-xs font-semibold text-text-primary">FIFA World Cup</p>
            <p className="text-[10px] text-text-secondary">2026 · USA · MEX · CAN</p>
          </div>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed left-0 top-0 z-40 h-screen w-64 flex-col bg-bg-secondary/80 backdrop-blur-xl border-r border-accent-gold/10">
        {sidebarContent}
      </aside>

      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-xl bg-bg-secondary/80 backdrop-blur-xl border border-accent-gold/10 text-text-primary"
        aria-label="Abrir menú"
      >
        <Menu className="w-6 h-6" />
      </button>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="lg:hidden fixed left-0 top-0 z-50 h-screen w-64 flex flex-col bg-bg-secondary/95 backdrop-blur-xl border-r border-accent-gold/10"
            >
              <button
                onClick={() => setMobileOpen(false)}
                className="absolute top-4 right-4 p-2 rounded-lg text-text-secondary hover:text-text-primary transition-colors"
                aria-label="Cerrar menú"
              >
                <X className="w-5 h-5" />
              </button>
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
