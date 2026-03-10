'use client';

import { useCallback } from 'react';
import {
  AlertTriangle,
  Info,
  AlertOctagon,
  Check,
  Bell,
  Route,
  Clock,
  Mail,
  Flag,
  ChevronDown,
} from 'lucide-react';
import { clsx } from 'clsx';
import type { Alert, AlertSeverity, AlertType } from '@/lib/types';

// ── Severity styling ──────────────────────────────────────────────────────────

const SEVERITY_CONFIG: Record<
  AlertSeverity,
  { icon: React.ReactNode; border: string; bg: string; iconColor: string }
> = {
  info: {
    icon: <Info size={14} />,
    border: 'border-blue-500/30',
    bg: 'bg-blue-500/5',
    iconColor: 'text-blue-400',
  },
  warning: {
    icon: <AlertTriangle size={14} />,
    border: 'border-yellow-500/30',
    bg: 'bg-yellow-500/5',
    iconColor: 'text-yellow-400',
  },
  critical: {
    icon: <AlertOctagon size={14} />,
    border: 'border-red-500/30',
    bg: 'bg-red-500/10',
    iconColor: 'text-red-400',
  },
};

// ── Alert type icons ──────────────────────────────────────────────────────────

const TYPE_ICONS: Record<AlertType, React.ReactNode> = {
  risk_zone_entry: <AlertTriangle size={12} />,
  delay: <Clock size={12} />,
  route_deviation: <Route size={12} />,
  email_received: <Mail size={12} />,
  milestone: <Flag size={12} />,
  action_item_due: <Bell size={12} />,
};

// ── Time formatting ───────────────────────────────────────────────────────────

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ── Alert item ────────────────────────────────────────────────────────────────

interface AlertItemProps {
  alert: Alert;
  onAcknowledge: (id: string) => void;
}

function AlertItem({ alert, onAcknowledge }: AlertItemProps) {
  const severity = SEVERITY_CONFIG[alert.severity];
  const typeIcon = TYPE_ICONS[alert.alert_type] ?? <Bell size={12} />;

  const handleAcknowledge = useCallback(() => {
    onAcknowledge(alert.id);
  }, [alert.id, onAcknowledge]);

  return (
    <div
      className={clsx(
        'group relative rounded-lg border px-3 py-2.5 transition-colors',
        severity.border,
        severity.bg,
        alert.acknowledged && 'opacity-50',
      )}
    >
      <div className="flex items-start gap-2.5">
        {/* Severity icon */}
        <div className={clsx('mt-0.5 shrink-0', severity.iconColor)}>
          {severity.icon}
        </div>

        <div className="min-w-0 flex-1">
          {/* Title row */}
          <div className="flex items-center gap-2">
            <h4 className="truncate text-sm font-medium text-slate-200">
              {alert.title}
            </h4>
            <span className="shrink-0 text-slate-600">{typeIcon}</span>
          </div>

          {/* Message */}
          <p className="mt-0.5 line-clamp-2 text-xs text-slate-400">
            {alert.message}
          </p>

          {/* Meta row */}
          <div className="mt-1.5 flex items-center gap-3 text-xs text-slate-500">
            <span>{timeAgo(alert.created_at)}</span>
            {alert.vessel_name && (
              <span className="truncate">{alert.vessel_name}</span>
            )}
            {alert.contract_id && (
              <span className="truncate font-mono">{alert.contract_id}</span>
            )}
          </div>
        </div>

        {/* Acknowledge button */}
        {!alert.acknowledged && (
          <button
            onClick={handleAcknowledge}
            className="shrink-0 rounded-md p-1.5 text-slate-500 opacity-0 transition-all hover:bg-slate-700/50 hover:text-green-400 group-hover:opacity-100"
            aria-label="Acknowledge alert"
            title="Acknowledge"
          >
            <Check size={14} />
          </button>
        )}
      </div>
    </div>
  );
}

// ── Feed component ────────────────────────────────────────────────────────────

interface AlertFeedProps {
  alerts: Alert[];
  onAcknowledge: (id: string) => void;
}

export function AlertFeed({ alerts, onAcknowledge }: AlertFeedProps) {
  const unacked = alerts.filter((a) => !a.acknowledged);
  const acked = alerts.filter((a) => a.acknowledged);

  return (
    <div className="flex h-full w-64 flex-col overflow-hidden rounded-xl bg-slate-800/80 shadow-2xl backdrop-blur-md border border-slate-700/40 lg:w-72">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-700/50 px-4 py-3">
        <div className="flex items-center gap-2">
          <Bell size={14} className="text-slate-400" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Alerts
          </h3>
        </div>
        {unacked.length > 0 && (
          <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-red-500/20 px-1.5 text-xs font-semibold text-red-400">
            {unacked.length}
          </span>
        )}
      </div>

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-slate-700">
        {alerts.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-slate-500">
            <Bell size={24} className="mb-2 opacity-40" />
            <p className="text-xs">No alerts</p>
          </div>
        )}

        {/* Unacknowledged first */}
        {unacked.map((alert) => (
          <div key={alert.id} className="animate-fade-in">
            <AlertItem alert={alert} onAcknowledge={onAcknowledge} />
          </div>
        ))}

        {/* Divider between acked and unacked */}
        {unacked.length > 0 && acked.length > 0 && (
          <div className="flex items-center gap-2 py-1">
            <div className="h-px flex-1 bg-slate-700/50" />
            <span className="flex items-center gap-1 text-xs text-slate-600">
              <ChevronDown size={10} />
              Acknowledged
            </span>
            <div className="h-px flex-1 bg-slate-700/50" />
          </div>
        )}

        {acked.map((alert) => (
          <AlertItem key={alert.id} alert={alert} onAcknowledge={onAcknowledge} />
        ))}
      </div>
    </div>
  );
}
