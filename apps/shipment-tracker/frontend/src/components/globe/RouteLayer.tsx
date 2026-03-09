'use client';

import { ArcLayer } from '@deck.gl/layers';
import type { ActiveShipment } from '@/lib/types';

interface RouteSegment {
  id: string;
  sourcePosition: [number, number];
  targetPosition: [number, number];
  sourceColor: [number, number, number, number];
  targetColor: [number, number, number, number];
  isSelected: boolean;
}

interface RouteLayerOptions {
  shipments: ActiveShipment[];
  selectedShipmentId: string | null;
}

/**
 * Creates deck.gl ArcLayer(s) that draw great-circle route arcs.
 *
 * For each shipment we draw two arcs:
 *   1. Load port -> current vessel position  (completed portion, brighter)
 *   2. Current vessel position -> discharge port (remaining portion, dimmer)
 *
 * If the vessel has no known position, a single arc from load to discharge is drawn.
 */
export function createRouteLayers({ shipments, selectedShipmentId }: RouteLayerOptions) {
  const segments: RouteSegment[] = [];

  for (const s of shipments) {
    const isSelected = s.id === selectedShipmentId;
    const alpha = isSelected ? 200 : 100;

    if (s.vessel_lat !== null && s.vessel_lon !== null) {
      // Completed portion: load port -> vessel
      segments.push({
        id: `${s.id}-completed`,
        sourcePosition: [s.load_port_lon, s.load_port_lat],
        targetPosition: [s.vessel_lon, s.vessel_lat],
        sourceColor: [34, 197, 94, alpha],  // green (origin)
        targetColor: [59, 130, 246, alpha],  // blue (mid-route)
        isSelected,
      });

      // Remaining portion: vessel -> discharge port
      segments.push({
        id: `${s.id}-remaining`,
        sourcePosition: [s.vessel_lon, s.vessel_lat],
        targetPosition: [s.discharge_port_lon, s.discharge_port_lat],
        sourceColor: [59, 130, 246, alpha],        // blue (mid-route)
        targetColor: [147, 51, 234, alpha * 0.7],  // purple-ish (destination, dimmer)
        isSelected,
      });
    } else {
      // Full route: load -> discharge (no vessel position known)
      segments.push({
        id: `${s.id}-full`,
        sourcePosition: [s.load_port_lon, s.load_port_lat],
        targetPosition: [s.discharge_port_lon, s.discharge_port_lat],
        sourceColor: [34, 197, 94, alpha * 0.6],
        targetColor: [147, 51, 234, alpha * 0.6],
        isSelected,
      });
    }
  }

  return new ArcLayer<RouteSegment>({
    id: 'route-layer',
    data: segments,
    getSourcePosition: (d) => d.sourcePosition,
    getTargetPosition: (d) => d.targetPosition,
    getSourceColor: (d) => d.sourceColor,
    getTargetColor: (d) => d.targetColor,
    getWidth: (d) => (d.isSelected ? 3 : 1.5),
    greatCircle: true,
    numSegments: 50,
    widthMinPixels: 1,
    widthMaxPixels: 4,
    updateTriggers: {
      getWidth: [selectedShipmentId],
      getSourceColor: [selectedShipmentId],
      getTargetColor: [selectedShipmentId],
    },
  });
}
