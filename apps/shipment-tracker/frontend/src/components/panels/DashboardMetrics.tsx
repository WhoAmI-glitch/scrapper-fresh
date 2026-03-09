'use client';

import {
  Ship,
  Package,
  DollarSign,
  AlertTriangle,
  Anchor,
} from 'lucide-react';
import type { DashboardMetrics as DashboardMetricsType } from '@/lib/types';

function formatTons(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString();
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toLocaleString()}`;
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtext?: string;
  highlight?: boolean;
}

function MetricCard({ icon, label, value, subtext, highlight }: MetricCardProps) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-slate-800/60 px-4 py-2.5 backdrop-blur-sm border border-slate-700/40">
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
          highlight
            ? 'bg-red-500/20 text-red-400'
            : 'bg-blue-500/20 text-blue-400'
        }`}
      >
        {icon}
      </div>
      <div className="min-w-0">
        <p className="truncate text-xs font-medium text-slate-400">{label}</p>
        <p className="text-lg font-semibold leading-tight text-white">{value}</p>
        {subtext && (
          <p className="truncate text-xs text-slate-500">{subtext}</p>
        )}
      </div>
    </div>
  );
}

interface DashboardMetricsProps {
  metrics: DashboardMetricsType | null;
  alertCount: number;
}

export function DashboardMetrics({ metrics, alertCount }: DashboardMetricsProps) {
  if (!metrics) {
    return (
      <div className="flex w-full items-center gap-3 px-4 py-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="h-16 flex-1 animate-pulse rounded-lg bg-slate-800/40"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="flex w-full items-stretch gap-3 overflow-x-auto px-4 py-3 scrollbar-hide">
      <MetricCard
        icon={<Ship size={18} />}
        label="Active Shipments"
        value={metrics.active_shipments.toString()}
        subtext={`${metrics.active_vessels} vessels tracked`}
      />
      <MetricCard
        icon={<Package size={18} />}
        label="Tons at Sea"
        value={formatTons(metrics.total_tons_at_sea)}
        subtext="total cargo"
      />
      <MetricCard
        icon={<DollarSign size={18} />}
        label="Value at Sea"
        value={formatCurrency(metrics.total_value_at_sea)}
        subtext="contract value"
      />
      <MetricCard
        icon={<AlertTriangle size={18} />}
        label="Risk Exposure"
        value={metrics.vessels_in_risk_zones.toString()}
        subtext="vessels in risk zones"
        highlight={metrics.vessels_in_risk_zones > 0}
      />
      <MetricCard
        icon={<Anchor size={18} />}
        label="Unread Alerts"
        value={alertCount.toString()}
        highlight={alertCount > 0}
      />
    </div>
  );
}
