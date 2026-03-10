'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Globe2,
  BarChart3,
  Ship,
  Handshake,
  Calendar,
  Bell,
  FileSpreadsheet,
  ChevronLeft,
  ChevronRight,
  Search,
  Users,
  Brain,
} from 'lucide-react';
import clsx from 'clsx';

const NAV_ITEMS = [
  { href: '/', label: 'Globe', icon: Globe2 },
  { href: '/deals', label: 'Deals', icon: BarChart3 },
  { href: '/shipments', label: 'Shipments', icon: Ship },
  { href: '/counterparties', label: 'Counterparties', icon: Users },
  { href: '/meetings', label: 'Meetings', icon: Calendar },
  { href: '/intelligence', label: 'AI Intel', icon: Brain },
  { href: '/alerts', label: 'Alerts', icon: Bell },
  { href: '/reports', label: 'Reports', icon: FileSpreadsheet },
];

interface SidebarProps {
  onSearch?: () => void;
}

export function Sidebar({ onSearch }: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={clsx(
        'flex h-full flex-col border-r border-zinc-800/60 bg-zinc-950 transition-all duration-200',
        collapsed ? 'w-16' : 'w-56'
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 border-b border-zinc-800/60 px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600">
          <Ship size={16} className="text-white" />
        </div>
        {!collapsed && (
          <span className="truncate text-sm font-semibold text-zinc-100">
            Charcoal Intel
          </span>
        )}
      </div>

      {/* Search shortcut */}
      <div className="px-2 pt-3 pb-1">
        <button
          onClick={onSearch}
          className={clsx(
            'flex w-full items-center gap-2 rounded-lg border border-zinc-800/60 px-3 py-2 text-sm text-zinc-500 transition-colors hover:border-zinc-700 hover:text-zinc-300',
            collapsed && 'justify-center px-0'
          )}
        >
          <Search size={14} />
          {!collapsed && (
            <>
              <span className="flex-1 text-left">Search...</span>
              <kbd className="rounded border border-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-600">
                ⌘K
              </kbd>
            </>
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-2">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors',
                active
                  ? 'bg-zinc-800/80 text-zinc-100 font-medium'
                  : 'text-zinc-400 hover:bg-zinc-800/40 hover:text-zinc-200',
                collapsed && 'justify-center px-0'
              )}
            >
              <Icon size={18} className={active ? 'text-blue-400' : ''} />
              {!collapsed && <span>{label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-zinc-800/60 p-2">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex w-full items-center justify-center rounded-lg py-2 text-zinc-500 transition-colors hover:bg-zinc-800/40 hover:text-zinc-300"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  );
}
