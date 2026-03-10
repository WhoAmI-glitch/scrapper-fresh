'use client';

import { Bell, Check, AlertTriangle, Info, ShieldAlert } from 'lucide-react';
import clsx from 'clsx';
import { useAlerts } from '@/hooks/useAlerts';
import type { Alert, AlertSeverity } from '@/lib/types';

const SEVERITY_STYLES: Record<AlertSeverity, { border: string; icon: string; dot: string }> = {
  critical: { border: 'border-l-red-500', icon: 'text-red-400', dot: 'bg-red-400' },
  warning: { border: 'border-l-amber-500', icon: 'text-amber-400', dot: 'bg-amber-400' },
  info: { border: 'border-l-blue-500', icon: 'text-blue-400', dot: 'bg-blue-400' },
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function AlertsPage() {
  const { alerts, unacknowledgedCount, acknowledge } = useAlerts();

  return (
    <div className="flex h-full flex-col overflow-hidden bg-zinc-950">
      <div className="flex items-center justify-between border-b border-zinc-800/60 px-6 py-4">
        <div>
          <h1 className="flex items-center gap-2 text-lg font-semibold text-zinc-100">
            <Bell size={20} className="text-blue-400" />
            Alerts
          </h1>
          <p className="mt-0.5 text-sm text-zinc-500">
            {unacknowledgedCount} unacknowledged · {alerts.length} total
          </p>
        </div>
      </div>

      <div className="flex-1 space-y-2 overflow-auto p-6">
        {alerts.map((alert) => (
          <AlertRow key={alert.id} alert={alert} onAcknowledge={acknowledge} />
        ))}
        {alerts.length === 0 && (
          <div className="flex h-64 items-center justify-center text-sm text-zinc-600">
            No alerts
          </div>
        )}
      </div>
    </div>
  );
}

function AlertRow({ alert, onAcknowledge }: { alert: Alert; onAcknowledge: (id: string) => void }) {
  const style = SEVERITY_STYLES[alert.severity];
  const SevIcon = alert.severity === 'critical' ? ShieldAlert : alert.severity === 'warning' ? AlertTriangle : Info;

  return (
    <div
      className={clsx(
        'flex items-start gap-3 rounded-lg border-l-2 bg-zinc-900/50 p-4 transition-colors hover:bg-zinc-800/50',
        style.border,
        alert.acknowledged && 'opacity-50'
      )}
    >
      <SevIcon size={16} className={clsx('mt-0.5 shrink-0', style.icon)} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-zinc-200">{alert.title}</span>
          {!alert.acknowledged && (
            <span className={clsx('h-1.5 w-1.5 rounded-full', style.dot)} />
          )}
        </div>
        <p className="mt-0.5 text-xs text-zinc-500 line-clamp-2">{alert.message}</p>
        <div className="mt-1.5 flex items-center gap-3 text-[11px] text-zinc-600">
          <span>{timeAgo(alert.created_at)}</span>
          {alert.contract_id && <span>{alert.contract_id}</span>}
          {alert.vessel_name && <span>{alert.vessel_name}</span>}
        </div>
      </div>

      {!alert.acknowledged && (
        <button
          onClick={() => onAcknowledge(alert.id)}
          className="shrink-0 rounded-lg border border-zinc-700/50 p-1.5 text-zinc-500 transition-colors hover:border-zinc-600 hover:text-zinc-300"
        >
          <Check size={14} />
        </button>
      )}
    </div>
  );
}
