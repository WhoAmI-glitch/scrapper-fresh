'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, X, Globe2, BarChart3, Ship, Users, Calendar, Bell, FileSpreadsheet } from 'lucide-react';
import { Sidebar } from './Sidebar';

const CMD_ITEMS = [
  { label: 'Globe Dashboard', href: '/', icon: Globe2 },
  { label: 'Deals Pipeline', href: '/deals', icon: BarChart3 },
  { label: 'Shipments', href: '/shipments', icon: Ship },
  { label: 'Counterparties', href: '/counterparties', icon: Users },
  { label: 'Meetings', href: '/meetings', icon: Calendar },
  { label: 'Alerts', href: '/alerts', icon: Bell },
  { label: 'Reports & Export', href: '/reports', icon: FileSpreadsheet },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [cmdOpen, setCmdOpen] = useState(false);
  const [query, setQuery] = useState('');

  const openCmd = useCallback(() => {
    setCmdOpen(true);
    setQuery('');
  }, []);

  const closeCmd = useCallback(() => setCmdOpen(false), []);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCmdOpen((prev) => !prev);
        setQuery('');
      }
      if (e.key === 'Escape' && cmdOpen) {
        closeCmd();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [cmdOpen, closeCmd]);

  const filtered = query
    ? CMD_ITEMS.filter((item) =>
        item.label.toLowerCase().includes(query.toLowerCase())
      )
    : CMD_ITEMS;

  function navigate(href: string) {
    router.push(href);
    closeCmd();
  }

  return (
    <div className="flex h-full">
      <Sidebar onSearch={openCmd} />

      <main className="flex-1 overflow-hidden">
        {children}
      </main>

      {/* Command Palette */}
      {cmdOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/60 backdrop-blur-sm"
          onClick={closeCmd}
        >
          <div
            className="w-full max-w-lg overflow-hidden rounded-xl border border-zinc-700/50 bg-zinc-900 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 border-b border-zinc-800 px-4 py-3">
              <Search size={16} className="text-zinc-500" />
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search pages, deals, vessels..."
                className="flex-1 bg-transparent text-sm text-zinc-100 placeholder-zinc-500 outline-none"
              />
              <button onClick={closeCmd}>
                <X size={14} className="text-zinc-500 hover:text-zinc-300" />
              </button>
            </div>
            <div className="max-h-72 overflow-y-auto p-2">
              {filtered.length === 0 && (
                <p className="px-3 py-6 text-center text-sm text-zinc-500">
                  No results found
                </p>
              )}
              {filtered.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.href}
                    onClick={() => navigate(item.href)}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-300 transition-colors hover:bg-zinc-800"
                  >
                    <Icon size={16} className="text-zinc-500" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
            <div className="border-t border-zinc-800 px-4 py-2 text-[11px] text-zinc-600">
              <kbd className="rounded border border-zinc-700 px-1 py-0.5">↑↓</kbd> navigate
              <span className="mx-2">·</span>
              <kbd className="rounded border border-zinc-700 px-1 py-0.5">↵</kbd> open
              <span className="mx-2">·</span>
              <kbd className="rounded border border-zinc-700 px-1 py-0.5">esc</kbd> close
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
