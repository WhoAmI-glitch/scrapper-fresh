'use client';

import { useState } from 'react';
import { FileSpreadsheet, Download, TrendingUp, Ship as ShipIcon, DollarSign, Globe2, BarChart3 } from 'lucide-react';
import useSWR from 'swr';
import clsx from 'clsx';
import { api } from '@/lib/api';
import type { DealPnL } from '@/lib/types';

function formatMoney(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

const REPORTS = [
  { key: 'trading-book', label: 'Trading Book', desc: 'Full P&L + positions + exposure', icon: TrendingUp },
  { key: 'shipment-progress', label: 'Shipment Progress', desc: 'Milestones, delays, and progress bars', icon: ShipIcon },
];

export default function ReportsPage() {
  const [downloading, setDownloading] = useState<string | null>(null);

  const { data: pnlData } = useSWR('pnl', () => api.getDealsPnl());
  const pnlItems = pnlData?.items ?? [];

  async function handleExport(type: 'trading-book' | 'shipment-progress') {
    setDownloading(type);
    try {
      const res = await fetch(api.getExportUrl(type), { method: 'POST' });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type.replace('-', '_')}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div className="flex h-full flex-col overflow-hidden bg-zinc-950">
      <div className="border-b border-zinc-800/60 px-6 py-4">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-zinc-100">
          <FileSpreadsheet size={20} className="text-blue-400" />
          Reports & Export
        </h1>
        <p className="mt-0.5 text-sm text-zinc-500">
          Generate Excel workbooks and view P&L analysis
        </p>
      </div>

      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Quick Exports */}
        <section>
          <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">
            Quick Exports
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {REPORTS.map(({ key, label, desc, icon: Icon }) => (
              <button
                key={key}
                onClick={() => handleExport(key as 'trading-book' | 'shipment-progress')}
                disabled={downloading === key}
                className="flex items-center gap-4 rounded-xl border border-zinc-800/60 bg-zinc-900/50 p-4 text-left transition-colors hover:border-zinc-700/60 disabled:opacity-50"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-zinc-800">
                  <Icon size={18} className="text-zinc-400" />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-zinc-200">{label}</div>
                  <div className="text-xs text-zinc-500">{desc}</div>
                </div>
                <Download
                  size={16}
                  className={clsx(
                    'text-zinc-500',
                    downloading === key && 'animate-bounce'
                  )}
                />
              </button>
            ))}
          </div>
        </section>

        {/* P&L Preview */}
        {pnlItems.length > 0 && (
          <section>
            <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">
              Deal P&L Summary
            </h2>
            <div className="overflow-x-auto rounded-xl border border-zinc-800/60">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-800/60 bg-zinc-900/50">
                    {['Contract', 'Revenue', 'Total Costs', 'Gross Margin', 'Margin %', 'Commission', 'Net Margin'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/40">
                  {pnlItems.map((pnl) => (
                    <tr key={pnl.deal_id} className="transition-colors hover:bg-zinc-900/50">
                      <td className="px-4 py-3 font-medium text-zinc-200">{pnl.contract_id}</td>
                      <td className="px-4 py-3 text-zinc-300">{formatMoney(pnl.revenue)}</td>
                      <td className="px-4 py-3 text-zinc-400">{formatMoney(pnl.total_costs)}</td>
                      <td className={clsx(
                        'px-4 py-3 font-medium',
                        pnl.gross_margin >= 0 ? 'text-green-400' : 'text-red-400'
                      )}>
                        {formatMoney(pnl.gross_margin)}
                      </td>
                      <td className="px-4 py-3 text-zinc-400">{pnl.margin_pct.toFixed(1)}%</td>
                      <td className="px-4 py-3 text-zinc-500">{formatMoney(pnl.total_commission)}</td>
                      <td className={clsx(
                        'px-4 py-3 font-medium',
                        pnl.net_margin >= 0 ? 'text-green-400' : 'text-red-400'
                      )}>
                        {formatMoney(pnl.net_margin)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
