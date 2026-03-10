'use client';

import useSWR from 'swr';
import { Users, Building2, Globe2, Mail, Phone } from 'lucide-react';
import clsx from 'clsx';
import { api } from '@/lib/api';
import type { Counterparty } from '@/lib/types';

const TYPE_COLORS: Record<string, string> = {
  buyer: 'bg-blue-500/10 text-blue-400',
  seller: 'bg-green-500/10 text-green-400',
  broker: 'bg-purple-500/10 text-purple-400',
  agent: 'bg-amber-500/10 text-amber-400',
};

export default function CounterpartiesPage() {
  const { data } = useSWR('counterparties', () => api.getCounterparties(1, 100), {
    refreshInterval: 60_000,
  });

  const items = data?.items ?? [];

  return (
    <div className="flex h-full flex-col overflow-hidden bg-zinc-950">
      <div className="flex items-center justify-between border-b border-zinc-800/60 px-6 py-4">
        <div>
          <h1 className="flex items-center gap-2 text-lg font-semibold text-zinc-100">
            <Users size={20} className="text-blue-400" />
            Counterparties
          </h1>
          <p className="mt-0.5 text-sm text-zinc-500">
            {items.length} trading partners
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((cp) => (
            <CounterpartyCard key={cp.id} counterparty={cp} />
          ))}
        </div>
        {items.length === 0 && (
          <div className="flex h-64 items-center justify-center text-sm text-zinc-600">
            No counterparties found
          </div>
        )}
      </div>
    </div>
  );
}

function CounterpartyCard({ counterparty: cp }: { counterparty: Counterparty }) {
  return (
    <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/50 p-4 transition-colors hover:border-zinc-700/60">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-800">
            <Building2 size={16} className="text-zinc-400" />
          </div>
          <div>
            <div className="text-sm font-medium text-zinc-100">{cp.name}</div>
            {cp.short_name && (
              <div className="text-xs text-zinc-500">{cp.short_name}</div>
            )}
          </div>
        </div>
        <span className={clsx('rounded-full px-2 py-0.5 text-[11px] font-medium', TYPE_COLORS[cp.type])}>
          {cp.type}
        </span>
      </div>

      <div className="mt-3 space-y-1.5">
        {cp.country && (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Globe2 size={11} />
            <span>{cp.country}</span>
          </div>
        )}
        {cp.primary_contact_email && (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Mail size={11} />
            <span className="truncate">{cp.primary_contact_email}</span>
          </div>
        )}
        {cp.primary_contact_phone && (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Phone size={11} />
            <span>{cp.primary_contact_phone}</span>
          </div>
        )}
      </div>

      <div className="mt-3 border-t border-zinc-800/60 pt-2">
        <span className="text-xs text-zinc-600">
          {cp.deal_count} deal{cp.deal_count !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
}
