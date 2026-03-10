'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { BarChart3, Download, Table2, LayoutGrid } from 'lucide-react';
import clsx from 'clsx';
import { api } from '@/lib/api';
import type { Deal, DealStatus } from '@/lib/types';

const STATUS_COLUMNS: DealStatus[] = ['draft', 'confirmed', 'loading', 'in_transit', 'arrived', 'completed'];

const STATUS_COLORS: Record<DealStatus, string> = {
  draft: 'border-zinc-600',
  confirmed: 'border-blue-500',
  loading: 'border-amber-500',
  in_transit: 'border-cyan-500',
  arrived: 'border-green-500',
  completed: 'border-emerald-600',
  cancelled: 'border-red-500',
};

const RISK_DOT: Record<string, string> = {
  low: 'bg-green-400',
  medium: 'bg-amber-400',
  high: 'bg-orange-400',
  critical: 'bg-red-400',
};

function formatMoney(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

export default function DealsPage() {
  const [view, setView] = useState<'kanban' | 'table'>('kanban');
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  const { data } = useSWR('deals', () => api.getDeals(1, 100, statusFilter), {
    refreshInterval: 30_000,
  });

  const { data: exposureData } = useSWR('exposure', () => api.getExposureByRegion());

  const deals = data?.items ?? [];
  const totalValue = deals.reduce((sum, d) => sum + (d.contract_value || 0), 0);

  return (
    <div className="flex h-full flex-col overflow-hidden bg-zinc-950">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800/60 px-6 py-4">
        <div>
          <h1 className="flex items-center gap-2 text-lg font-semibold text-zinc-100">
            <BarChart3 size={20} className="text-blue-400" />
            Deals
          </h1>
          <p className="mt-0.5 text-sm text-zinc-500">
            {deals.length} active · {formatMoney(totalValue)} total exposure
          </p>
        </div>
        <div className="flex items-center gap-2">
          <a
            href={api.getExportUrl('trading-book')}
            target="_blank"
            rel="noopener"
            className="flex items-center gap-1.5 rounded-lg border border-zinc-700/50 px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:border-zinc-600 hover:text-zinc-200"
            onClick={(e) => {
              e.preventDefault();
              fetch(api.getExportUrl('trading-book'), { method: 'POST' })
                .then(r => r.blob())
                .then(b => {
                  const url = URL.createObjectURL(b);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'trading_book.xlsx';
                  a.click();
                  URL.revokeObjectURL(url);
                });
            }}
          >
            <Download size={12} /> Export
          </a>
          <div className="flex rounded-lg border border-zinc-800">
            <button
              onClick={() => setView('kanban')}
              className={clsx(
                'rounded-l-lg px-2 py-1.5',
                view === 'kanban' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'
              )}
            >
              <LayoutGrid size={14} />
            </button>
            <button
              onClick={() => setView('table')}
              className={clsx(
                'rounded-r-lg px-2 py-1.5',
                view === 'table' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'
              )}
            >
              <Table2 size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {view === 'kanban' ? (
          <KanbanView deals={deals} />
        ) : (
          <TableView deals={deals} />
        )}

        {/* Exposure summary */}
        {exposureData && exposureData.length > 0 && (
          <div className="mt-6 rounded-xl border border-zinc-800/60 bg-zinc-900/50 p-4">
            <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">
              Exposure by Region
            </h3>
            <div className="space-y-2">
              {exposureData.map((exp) => {
                const pct = totalValue > 0 ? (exp.total_value / totalValue) * 100 : 0;
                return (
                  <div key={exp.region} className="flex items-center gap-3">
                    <span className="w-28 text-sm text-zinc-300">{exp.region}</span>
                    <div className="flex-1 h-2 rounded-full bg-zinc-800">
                      <div
                        className="h-2 rounded-full bg-blue-500"
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                    <span className="w-16 text-right text-xs text-zinc-500">
                      {formatMoney(exp.total_value)}
                    </span>
                    <span className="w-10 text-right text-xs text-zinc-600">
                      {pct.toFixed(0)}%
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function KanbanView({ deals }: { deals: Deal[] }) {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {STATUS_COLUMNS.map((status) => {
        const colDeals = deals.filter((d) => d.status === status);
        return (
          <div key={status} className="flex w-64 shrink-0 flex-col">
            <div className="mb-3 flex items-center gap-2">
              <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                {status.replace('_', ' ')}
              </span>
              <span className="rounded-full bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-500">
                {colDeals.length}
              </span>
            </div>
            <div className="space-y-2">
              {colDeals.map((deal) => (
                <div
                  key={deal.id}
                  className={clsx(
                    'rounded-lg border-l-2 bg-zinc-900/80 p-3 transition-colors hover:bg-zinc-800/80',
                    STATUS_COLORS[deal.status]
                  )}
                >
                  <div className="text-xs font-medium text-zinc-200">{deal.contract_id}</div>
                  <div className="mt-1 text-[11px] text-zinc-500">
                    {deal.load_port?.name?.split(' ').pop()} → {deal.discharge_port?.name?.split(' ').pop()}
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-zinc-400">
                      {deal.quantity_tons?.toLocaleString()} MT
                    </span>
                    <span className="text-xs font-medium text-zinc-300">
                      {formatMoney(deal.contract_value || 0)}
                    </span>
                  </div>
                </div>
              ))}
              {colDeals.length === 0 && (
                <div className="rounded-lg border border-dashed border-zinc-800 p-4 text-center text-xs text-zinc-700">
                  No deals
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TableView({ deals }: { deals: Deal[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-zinc-800/60">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800/60 bg-zinc-900/50">
            {['Contract', 'Buyer', 'Seller', 'Qty (MT)', 'Value', 'Incoterms', 'Status'].map(
              (h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800/40">
          {deals.map((deal) => (
            <tr key={deal.id} className="transition-colors hover:bg-zinc-900/50">
              <td className="px-4 py-3 font-medium text-zinc-200">{deal.contract_id}</td>
              <td className="px-4 py-3 text-zinc-400">{deal.buyer}</td>
              <td className="px-4 py-3 text-zinc-400">{deal.seller}</td>
              <td className="px-4 py-3 text-zinc-300">{deal.quantity_tons?.toLocaleString()}</td>
              <td className="px-4 py-3 font-medium text-zinc-200">
                {formatMoney(deal.contract_value || 0)}
              </td>
              <td className="px-4 py-3 text-zinc-500">{deal.incoterms}</td>
              <td className="px-4 py-3">
                <span
                  className={clsx(
                    'inline-block rounded-full px-2 py-0.5 text-[11px] font-medium',
                    deal.status === 'in_transit' && 'bg-cyan-500/10 text-cyan-400',
                    deal.status === 'loading' && 'bg-amber-500/10 text-amber-400',
                    deal.status === 'arrived' && 'bg-green-500/10 text-green-400',
                    deal.status === 'completed' && 'bg-emerald-500/10 text-emerald-400',
                    deal.status === 'draft' && 'bg-zinc-500/10 text-zinc-400',
                    deal.status === 'confirmed' && 'bg-blue-500/10 text-blue-400',
                    deal.status === 'cancelled' && 'bg-red-500/10 text-red-400',
                  )}
                >
                  {deal.status.replace('_', ' ')}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
