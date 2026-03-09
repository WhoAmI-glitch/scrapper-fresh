'use client';

import { Package, DollarSign, Ship, AlertTriangle } from 'lucide-react';
import type { DashboardMetrics } from '@/lib/types';

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}

function formatTons(value: number): string {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}

interface StatRowProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  highlight?: boolean;
}

function StatRow({ icon, label, value, highlight }: StatRowProps) {
  return (
    <div className="flex items-center justify-between gap-2 py-1.5">
      <div className="flex items-center gap-2 text-slate-400">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <span
        className={`text-sm font-semibold ${
          highlight ? 'text-red-400' : 'text-white'
        }`}
      >
        {value}
      </span>
    </div>
  );
}

interface DealSummaryProps {
  metrics: DashboardMetrics | null;
}

export function DealSummary({ metrics }: DealSummaryProps) {
  if (!metrics) {
    return (
      <div className="w-64 animate-pulse rounded-xl bg-slate-800/80 p-4 backdrop-blur-md border border-slate-700/40">
        <div className="mb-3 h-4 w-24 rounded bg-slate-700" />
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-6 rounded bg-slate-700/50" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-64 rounded-xl bg-slate-800/80 p-4 backdrop-blur-md border border-slate-700/40 shadow-2xl">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Fleet Overview
      </h3>
      <div className="divide-y divide-slate-700/50">
        <StatRow
          icon={<Ship size={14} />}
          label="Active Deals"
          value={metrics.active_shipments.toString()}
        />
        <StatRow
          icon={<Package size={14} />}
          label="Tons at Sea"
          value={`${formatTons(metrics.total_tons_at_sea)} t`}
        />
        <StatRow
          icon={<DollarSign size={14} />}
          label="Value at Sea"
          value={formatCurrency(metrics.total_value_at_sea)}
        />
        <StatRow
          icon={<AlertTriangle size={14} />}
          label="In Risk Zones"
          value={metrics.vessels_in_risk_zones.toString()}
          highlight={metrics.vessels_in_risk_zones > 0}
        />
      </div>
    </div>
  );
}
