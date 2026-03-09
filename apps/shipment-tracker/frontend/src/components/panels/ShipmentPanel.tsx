'use client';

import {
  X,
  Ship,
  Anchor,
  MapPin,
  Calendar,
  ArrowRight,
  Package,
  FileText,
  Clock,
  Navigation,
} from 'lucide-react';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { RiskIndicator } from '@/components/ui/RiskIndicator';
import type { ActiveShipment } from '@/lib/types';

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

interface InfoRowProps {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}

function InfoRow({ icon, label, value }: InfoRowProps) {
  return (
    <div className="flex items-start gap-2.5 py-2">
      <div className="mt-0.5 shrink-0 text-slate-500">{icon}</div>
      <div className="min-w-0 flex-1">
        <p className="text-xs text-slate-500">{label}</p>
        <div className="text-sm font-medium text-slate-200">{value}</div>
      </div>
    </div>
  );
}

interface ShipmentPanelProps {
  shipment: ActiveShipment;
  onClose: () => void;
}

export function ShipmentPanel({ shipment, onClose }: ShipmentPanelProps) {
  const s = shipment;

  return (
    <div className="animate-slide-in-right flex h-full w-80 flex-col overflow-hidden rounded-l-2xl bg-slate-900/95 shadow-2xl backdrop-blur-md border-l border-slate-700/40 lg:w-96">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-700/50 px-5 py-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Ship size={16} className="shrink-0 text-blue-400" />
            <h2 className="truncate text-base font-semibold text-white">
              {s.vessel_name ?? 'Unassigned Vessel'}
            </h2>
          </div>
          <p className="mt-0.5 text-xs text-slate-400">
            {s.imo_number ? `IMO ${s.imo_number}` : 'No IMO'}{' '}
            {s.mmsi ? `/ MMSI ${s.mmsi}` : ''}
          </p>
        </div>
        <button
          onClick={onClose}
          className="ml-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-700/50 hover:text-white"
          aria-label="Close panel"
        >
          <X size={18} />
        </button>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto px-5 py-3 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-slate-700">
        {/* Status and risk */}
        <div className="mb-4 flex items-center gap-2">
          <StatusBadge status={s.status} />
          <RiskIndicator level={s.current_risk_level} />
        </div>

        {/* Route */}
        <div className="mb-4 rounded-lg bg-slate-800/60 p-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Route
          </p>
          <div className="flex items-center gap-2 text-sm">
            <MapPin size={14} className="shrink-0 text-green-400" />
            <span className="text-slate-200">{s.load_port_name}</span>
            <span className="text-xs text-slate-600">({s.load_port_code})</span>
          </div>
          <div className="ml-1.5 border-l border-dashed border-slate-600 py-1 pl-4">
            <ArrowRight size={12} className="text-slate-600" />
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Anchor size={14} className="shrink-0 text-purple-400" />
            <span className="text-slate-200">{s.discharge_port_name}</span>
            <span className="text-xs text-slate-600">({s.discharge_port_code})</span>
          </div>
        </div>

        {/* Vessel details */}
        <div className="mb-4 space-y-0 divide-y divide-slate-700/30">
          <InfoRow
            icon={<Navigation size={14} />}
            label="Speed / Heading"
            value={`${s.vessel_speed.toFixed(1)} kn / ${s.vessel_heading.toFixed(0)}\u00B0`}
          />
          <InfoRow
            icon={<Clock size={14} />}
            label="Last AIS Update"
            value={
              <span>
                {formatDateTime(s.last_ais_update)}{' '}
                <span className="text-xs text-slate-500">
                  ({timeAgo(s.last_ais_update)})
                </span>
              </span>
            }
          />
          <InfoRow
            icon={<Calendar size={14} />}
            label="ETA"
            value={formatDate(s.eta)}
          />
        </div>

        {/* Cargo */}
        <div className="mb-4 rounded-lg bg-slate-800/60 p-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Cargo
          </p>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-xs text-slate-500">Commodity</p>
              <p className="font-medium text-slate-200">{s.commodity}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Quantity</p>
              <p className="font-medium text-slate-200">
                {s.cargo_quantity_tons.toLocaleString()} t
              </p>
            </div>
          </div>
        </div>

        {/* Contract */}
        <div className="mb-4 rounded-lg bg-slate-800/60 p-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Contract
          </p>
          <div className="space-y-2 text-sm">
            <InfoRow
              icon={<FileText size={14} />}
              label="Contract ID"
              value={s.contract_id}
            />
            <div className="flex items-center gap-2 text-sm">
              <span className="text-slate-200">{s.seller}</span>
              <ArrowRight size={12} className="text-slate-500" />
              <span className="text-slate-200">{s.buyer}</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-slate-500">Value</p>
                <p className="font-medium text-slate-200">
                  {formatCurrency(s.contract_value)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Incoterms</p>
                <p className="font-medium text-slate-200">{s.incoterms}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Dates */}
        <div className="mb-4 space-y-0 divide-y divide-slate-700/30">
          <InfoRow
            icon={<Package size={14} />}
            label="B/L Number"
            value={s.bill_of_lading ?? 'Pending'}
          />
          <InfoRow
            icon={<Calendar size={14} />}
            label="Load Date"
            value={formatDate(s.load_date)}
          />
          <InfoRow
            icon={<Calendar size={14} />}
            label="Departure Date"
            value={formatDate(s.departure_date)}
          />
        </div>

        {/* Position */}
        {s.vessel_lat != null && s.vessel_lon != null && (
          <div className="rounded-lg bg-slate-800/60 p-3">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Current Position
            </p>
            <p className="font-mono text-sm text-slate-300">
              {s.vessel_lat.toFixed(4)}, {s.vessel_lon.toFixed(4)}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
