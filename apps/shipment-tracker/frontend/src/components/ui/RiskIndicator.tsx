'use client';

import { clsx } from 'clsx';
import type { RiskLevel } from '@/lib/types';

const RISK_STYLES: Record<RiskLevel, { bg: string; text: string; dot: string; label: string }> = {
  low: {
    bg: 'bg-green-500/20',
    text: 'text-green-400',
    dot: 'bg-green-400',
    label: 'Low',
  },
  medium: {
    bg: 'bg-yellow-500/20',
    text: 'text-yellow-400',
    dot: 'bg-yellow-400',
    label: 'Medium',
  },
  high: {
    bg: 'bg-orange-500/20',
    text: 'text-orange-400',
    dot: 'bg-orange-400',
    label: 'High',
  },
  critical: {
    bg: 'bg-red-500/20',
    text: 'text-red-400',
    dot: 'bg-red-400',
    label: 'Critical',
  },
};

interface RiskIndicatorProps {
  level: RiskLevel;
  /** When true, render as a single pulsing dot without text */
  dotOnly?: boolean;
  className?: string;
}

export function RiskIndicator({ level, dotOnly = false, className }: RiskIndicatorProps) {
  const style = RISK_STYLES[level];

  if (dotOnly) {
    return (
      <span
        className={clsx('relative inline-flex h-2.5 w-2.5', className)}
        title={`Risk: ${style.label}`}
      >
        <span
          className={clsx(
            'absolute inline-flex h-full w-full rounded-full opacity-75',
            style.dot,
            level === 'critical' && 'animate-pulse-dot',
          )}
        />
        <span
          className={clsx('relative inline-flex h-2.5 w-2.5 rounded-full', style.dot)}
        />
      </span>
    );
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        style.bg,
        style.text,
        className,
      )}
    >
      <span
        className={clsx(
          'h-1.5 w-1.5 rounded-full',
          style.dot,
          level === 'critical' && 'animate-pulse-dot',
        )}
      />
      {style.label} Risk
    </span>
  );
}
