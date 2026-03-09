'use client';

import { IconLayer } from '@deck.gl/layers';
import type { ActiveShipment, RiskLevel } from '@/lib/types';
import type { PickingInfo } from '@deck.gl/core';

// Ship icon encoded as data URI so we avoid external asset dependencies.
// A simple triangle pointing up, rendered on a 64x64 canvas.
const SHIP_ICON_ATLAS = createShipIconAtlas();
const ICON_MAPPING = {
  ship: { x: 0, y: 0, width: 64, height: 64, anchorY: 32, mask: true },
};

const RISK_COLORS: Record<RiskLevel, [number, number, number, number]> = {
  low: [34, 197, 94, 220],       // green
  medium: [234, 179, 8, 220],    // yellow
  high: [249, 115, 22, 220],     // orange
  critical: [239, 68, 68, 220],  // red
};

/**
 * Builds a data URI containing a simple ship-shaped icon.
 * Using a data URI means no external files need to be served.
 */
function createShipIconAtlas(): string {
  if (typeof document === 'undefined') {
    // Return a 1x1 transparent pixel for SSR -- the layer is never rendered server-side
    return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==';
  }

  const size = 64;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  if (!ctx) return '';

  // Draw a ship-like shape (triangle with a flat bottom)
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.moveTo(size / 2, 4);          // top (bow)
  ctx.lineTo(size - 8, size - 8);   // bottom-right
  ctx.lineTo(size / 2, size - 14);  // bottom-center indent (stern)
  ctx.lineTo(8, size - 8);          // bottom-left
  ctx.closePath();
  ctx.fill();

  return canvas.toDataURL('image/png');
}

// Only include shipments that have a vessel with known coordinates
type PositionedShipment = ActiveShipment & {
  vessel_lat: number;
  vessel_lon: number;
};

interface VesselLayerOptions {
  shipments: ActiveShipment[];
  selectedShipmentId: string | null;
  onSelectShipment: (id: string | null) => void;
}

/**
 * Creates a deck.gl IconLayer that renders ship icons for each vessel.
 * Icons are colored by current risk level and rotate to match vessel heading.
 */
export function createVesselLayer({
  shipments,
  selectedShipmentId,
  onSelectShipment,
}: VesselLayerOptions) {
  const positioned = shipments.filter(
    (s): s is PositionedShipment => s.vessel_lat !== null && s.vessel_lon !== null,
  );

  return new IconLayer<PositionedShipment>({
    id: 'vessel-layer',
    data: positioned,
    pickable: true,
    iconAtlas: SHIP_ICON_ATLAS,
    iconMapping: ICON_MAPPING,
    getIcon: () => 'ship',
    getPosition: (d) => [d.vessel_lon, d.vessel_lat],
    getSize: (d) => (d.id === selectedShipmentId ? 40 : 28),
    getColor: (d) => RISK_COLORS[d.current_risk_level] ?? RISK_COLORS.low,
    getAngle: (d) => 360 - d.vessel_heading, // deck.gl rotates counter-clockwise
    sizeScale: 1,
    sizeUnits: 'pixels',
    sizeMinPixels: 16,
    sizeMaxPixels: 48,
    billboard: false,
    onClick: (info: PickingInfo<PositionedShipment>) => {
      if (info.object) {
        onSelectShipment(info.object.id);
      }
    },
    updateTriggers: {
      getSize: [selectedShipmentId],
    },
  });
}

/**
 * Generates tooltip content for a vessel hover event.
 */
export function getVesselTooltip(info: PickingInfo<PositionedShipment>): string | null {
  const d = info.object;
  if (!d) return null;

  const speed = d.vessel_speed.toFixed(1);
  const tons = d.cargo_quantity_tons.toLocaleString();

  return `${d.vessel_name ?? 'Unknown Vessel'}
IMO: ${d.imo_number ?? 'N/A'}
Speed: ${speed} kn
Cargo: ${tons} t ${d.commodity}
Risk: ${d.current_risk_level.toUpperCase()}`;
}
