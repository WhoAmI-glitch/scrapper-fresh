'use client';

import dynamic from 'next/dynamic';
import { useShipments } from '@/hooks/useShipments';
import { useAlerts } from '@/hooks/useAlerts';
import { DashboardMetrics } from '@/components/panels/DashboardMetrics';
import { DealSummary } from '@/components/panels/DealSummary';
import { ShipmentPanel } from '@/components/panels/ShipmentPanel';
import { AlertFeed } from '@/components/panels/AlertFeed';

// Dynamic import for the globe component to avoid SSR issues with Mapbox GL
// and deck.gl which require browser APIs (canvas, WebGL, etc.)
const ShipmentGlobe = dynamic(
  () => import('@/components/globe/ShipmentGlobe'),
  {
    ssr: false,
    loading: () => (
      <div className="absolute inset-0 flex items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-blue-500" />
          <span className="text-sm text-slate-400">
            Initializing globe...
          </span>
        </div>
      </div>
    ),
  },
);

export default function HomePage() {
  const {
    shipments,
    selectedShipment,
    selectedShipmentId,
    selectShipment,
    metrics,
    riskZones,
    isLoading,
    error,
  } = useShipments();

  const {
    alerts,
    unacknowledgedCount,
    acknowledge,
  } = useAlerts();

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-slate-950">
      {/* ── Globe (full viewport background) ────────────────────────────────── */}
      <ShipmentGlobe
        shipments={shipments}
        riskZones={riskZones}
        selectedShipmentId={selectedShipmentId}
        onSelectShipment={selectShipment}
      />

      {/* ── Overlay UI ──────────────────────────────────────────────────────── */}

      {/* Top bar: Dashboard metrics */}
      <div className="pointer-events-auto absolute inset-x-0 top-0 z-20">
        <DashboardMetrics metrics={metrics} alertCount={unacknowledgedCount} />
      </div>

      {/* Top-right: Deal summary card */}
      <div className="pointer-events-auto absolute right-4 top-20 z-20 hidden lg:block">
        <DealSummary metrics={metrics} />
      </div>

      {/* Bottom-right: Alert feed */}
      <div className="pointer-events-auto absolute bottom-4 right-4 z-20 hidden max-h-[50vh] md:flex">
        <AlertFeed alerts={alerts} onAcknowledge={acknowledge} />
      </div>

      {/* Right side: Shipment detail panel (when a vessel is selected) */}
      {selectedShipment && (
        <div className="pointer-events-auto absolute bottom-0 right-0 top-0 z-30">
          <ShipmentPanel
            shipment={selectedShipment}
            onClose={() => selectShipment(null)}
          />
        </div>
      )}

      {/* Mobile bottom bar for alerts (shown on small screens) */}
      <div className="pointer-events-auto absolute bottom-0 inset-x-0 z-20 md:hidden">
        <MobileAlertBar
          unacknowledgedCount={unacknowledgedCount}
          alerts={alerts}
          onAcknowledge={acknowledge}
        />
      </div>

      {/* Loading / Error overlays */}
      {isLoading && shipments.length === 0 && (
        <div className="absolute inset-0 z-40 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-600 border-t-blue-500" />
            <span className="text-sm text-slate-400">
              Loading shipment data...
            </span>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute bottom-20 left-4 z-40 max-w-sm animate-slide-in-up rounded-lg border border-red-500/30 bg-red-950/80 px-4 py-3 shadow-xl backdrop-blur-sm">
          <p className="text-sm font-medium text-red-400">
            Failed to load data
          </p>
          <p className="mt-1 text-xs text-red-400/70">
            Check that the API server is running. Retrying automatically...
          </p>
        </div>
      )}
    </div>
  );
}

// ── Mobile alert bar ──────────────────────────────────────────────────────────

interface MobileAlertBarProps {
  unacknowledgedCount: number;
  alerts: import('@/lib/types').Alert[];
  onAcknowledge: (id: string) => void;
}

function MobileAlertBar({ unacknowledgedCount, alerts, onAcknowledge }: MobileAlertBarProps) {
  const latestAlert = alerts.find((a) => !a.acknowledged);

  if (!latestAlert && unacknowledgedCount === 0) return null;

  return (
    <div className="mx-2 mb-2 rounded-xl border border-slate-700/50 bg-slate-900/90 px-4 py-3 backdrop-blur-md">
      {latestAlert ? (
        <div className="flex items-center gap-3">
          <div
            className={`h-2 w-2 shrink-0 rounded-full ${
              latestAlert.severity === 'critical'
                ? 'bg-red-400 animate-pulse-dot'
                : latestAlert.severity === 'warning'
                  ? 'bg-yellow-400'
                  : 'bg-blue-400'
            }`}
          />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm text-slate-200">
              {latestAlert.title}
            </p>
            <p className="truncate text-xs text-slate-500">
              {latestAlert.message}
            </p>
          </div>
          {unacknowledgedCount > 1 && (
            <span className="shrink-0 rounded-full bg-slate-700/60 px-2 py-0.5 text-xs text-slate-400">
              +{unacknowledgedCount - 1}
            </span>
          )}
          <button
            onClick={() => onAcknowledge(latestAlert.id)}
            className="shrink-0 rounded-md px-2 py-1 text-xs text-slate-400 transition-colors hover:bg-slate-700/50 hover:text-white"
          >
            Dismiss
          </button>
        </div>
      ) : null}
    </div>
  );
}
