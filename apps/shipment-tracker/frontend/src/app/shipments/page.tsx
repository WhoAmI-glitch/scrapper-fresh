'use client';

import useSWR from 'swr';
import { Ship, Download, MapPin, Clock, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';
import { api } from '@/lib/api';
import type { ActiveShipment, ShipmentStatus, RiskLevel } from '@/lib/types';

const MILESTONES: ShipmentStatus[] = ['loading', 'departed', 'in_transit', 'arriving', 'arrived', 'discharged'];

const RISK_COLORS: Record<RiskLevel, string> = {
  low: 'text-green-400 bg-green-400/10',
  medium: 'text-amber-400 bg-amber-400/10',
  high: 'text-orange-400 bg-orange-400/10',
  critical: 'text-red-400 bg-red-400/10',
};

function formatMoney(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

function getProgress(status: ShipmentStatus): number {
  const idx = MILESTONES.indexOf(status);
  return idx >= 0 ? ((idx + 1) / MILESTONES.length) * 100 : 0;
}

function timeUntil(eta: string | null): string {
  if (!eta) return 'N/A';
  const diff = new Date(eta).getTime() - Date.now();
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
  if (days < 0) return `${Math.abs(days)}d overdue`;
  if (days === 0) return 'Today';
  return `${days}d`;
}

export default function ShipmentsPage() {
  const { data: shipments } = useSWR('active-shipments', () => api.getActiveShipments(), {
    refreshInterval: 30_000,
  });

  const items = shipments ?? [];

  return (
    <div className="flex h-full flex-col overflow-hidden bg-zinc-950">
      <div className="flex items-center justify-between border-b border-zinc-800/60 px-6 py-4">
        <div>
          <h1 className="flex items-center gap-2 text-lg font-semibold text-zinc-100">
            <Ship size={20} className="text-blue-400" />
            Shipments
          </h1>
          <p className="mt-0.5 text-sm text-zinc-500">
            {items.length} active shipments
          </p>
        </div>
        <button
          onClick={() => {
            fetch(api.getExportUrl('shipment-progress'), { method: 'POST' })
              .then(r => r.blob())
              .then(b => {
                const url = URL.createObjectURL(b);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'shipment_progress.xlsx';
                a.click();
                URL.revokeObjectURL(url);
              });
          }}
          className="flex items-center gap-1.5 rounded-lg border border-zinc-700/50 px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:border-zinc-600 hover:text-zinc-200"
        >
          <Download size={12} /> Export
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-auto p-6">
        {items.map((s) => (
          <ShipmentCard key={s.id} shipment={s} />
        ))}
        {items.length === 0 && (
          <div className="flex h-64 items-center justify-center text-sm text-zinc-600">
            No active shipments
          </div>
        )}
      </div>
    </div>
  );
}

function ShipmentCard({ shipment: s }: { shipment: ActiveShipment }) {
  const progress = getProgress(s.status);
  const etaStr = timeUntil(s.eta);
  const isOverdue = etaStr.includes('overdue');

  return (
    <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/50 p-5 transition-colors hover:border-zinc-700/60">
      {/* Top row */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-zinc-100">{s.contract_id}</span>
            <span className="text-xs text-zinc-500">·</span>
            <span className="text-sm text-zinc-400">{s.vessel_name || 'TBN'}</span>
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-zinc-500">
            <MapPin size={11} />
            <span>{s.load_port_name} → {s.discharge_port_name}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-zinc-500">
              {s.cargo_quantity_tons.toLocaleString()} MT
            </div>
            <div className="text-sm font-medium text-zinc-200">
              {formatMoney(s.contract_value)}
            </div>
          </div>
          <span
            className={clsx(
              'rounded-full px-2 py-0.5 text-[11px] font-medium',
              RISK_COLORS[s.current_risk_level]
            )}
          >
            {s.current_risk_level}
          </span>
        </div>
      </div>

      {/* Milestone bar */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-[10px] text-zinc-600">
          {MILESTONES.map((m) => (
            <span
              key={m}
              className={clsx(
                'uppercase',
                m === s.status ? 'font-semibold text-blue-400' : ''
              )}
            >
              {m.replace('_', ' ')}
            </span>
          ))}
        </div>
        <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-zinc-800">
          <div
            className={clsx(
              'h-full rounded-full transition-all duration-500',
              isOverdue ? 'bg-red-500' : 'bg-blue-500'
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Bottom row */}
      <div className="mt-3 flex items-center gap-4 text-xs text-zinc-500">
        <div className="flex items-center gap-1">
          <Clock size={11} />
          <span>ETA: {s.eta ? new Date(s.eta).toLocaleDateString() : 'N/A'}</span>
        </div>
        <span
          className={clsx(
            'font-medium',
            isOverdue ? 'text-red-400' : 'text-zinc-400'
          )}
        >
          {etaStr}
        </span>
        {s.bill_of_lading && (
          <span>B/L: {s.bill_of_lading}</span>
        )}
        {s.vessel_speed > 0 && (
          <span>{s.vessel_speed.toFixed(1)} kn · {s.vessel_heading.toFixed(0)}°</span>
        )}
      </div>
    </div>
  );
}
