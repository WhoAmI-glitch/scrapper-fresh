'use client';

import { clsx } from 'clsx';
import type { ShipmentStatus, DealStatus } from '@/lib/types';

type Status = ShipmentStatus | DealStatus;

const STATUS_STYLES: Record<Status, { bg: string; text: string; label: string }> = {
  // Shipment statuses
  loading: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Loading' },
  departed: { bg: 'bg-indigo-500/20', text: 'text-indigo-400', label: 'Departed' },
  in_transit: { bg: 'bg-sky-500/20', text: 'text-sky-400', label: 'In Transit' },
  arriving: { bg: 'bg-amber-500/20', text: 'text-amber-400', label: 'Arriving' },
  arrived: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'Arrived' },
  discharged: { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Discharged' },
  // Deal statuses
  draft: { bg: 'bg-gray-500/20', text: 'text-gray-400', label: 'Draft' },
  confirmed: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Confirmed' },
  completed: { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Completed' },
  cancelled: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Cancelled' },
};

interface StatusBadgeProps {
  status: Status;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const style = STATUS_STYLES[status] ?? {
    bg: 'bg-gray-500/20',
    text: 'text-gray-400',
    label: status,
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        style.bg,
        style.text,
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {style.label}
    </span>
  );
}
