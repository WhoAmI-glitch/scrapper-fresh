'use client';

import { PolygonLayer } from '@deck.gl/layers';
import type { RiskZone, RiskLevel } from '@/lib/types';

const RISK_FILL_COLORS: Record<RiskLevel, [number, number, number, number]> = {
  low: [34, 197, 94, 30],       // green, very translucent
  medium: [234, 179, 8, 40],    // yellow
  high: [249, 115, 22, 50],     // orange
  critical: [239, 68, 68, 60],  // red
};

const RISK_LINE_COLORS: Record<RiskLevel, [number, number, number, number]> = {
  low: [34, 197, 94, 120],
  medium: [234, 179, 8, 140],
  high: [249, 115, 22, 160],
  critical: [239, 68, 68, 180],
};

interface RiskZoneLayerOptions {
  riskZones: RiskZone[];
}

/**
 * Creates a deck.gl PolygonLayer for rendering risk zone polygons on the globe.
 * Fills are semi-transparent and colored by risk level.
 * Borders become more visible on hover.
 */
export function createRiskZoneLayer({ riskZones }: RiskZoneLayerOptions) {
  return new PolygonLayer<RiskZone>({
    id: 'risk-zone-layer',
    data: riskZones,
    pickable: true,
    stroked: true,
    filled: true,
    extruded: false,
    wireframe: false,
    // GeoJSON polygon coordinates are [lon, lat] pairs in nested arrays
    getPolygon: (d) => d.coordinates[0] as [number, number][],
    getFillColor: (d) => RISK_FILL_COLORS[d.risk_level] ?? RISK_FILL_COLORS.low,
    getLineColor: (d) => RISK_LINE_COLORS[d.risk_level] ?? RISK_LINE_COLORS.low,
    getLineWidth: 1,
    lineWidthMinPixels: 1,
    lineWidthMaxPixels: 3,

    // Slightly increase opacity on hover
    autoHighlight: true,
    highlightColor: [255, 255, 255, 40],
  });
}

/**
 * Generates a tooltip for risk zone hover.
 */
export function getRiskZoneTooltip(info: { object?: RiskZone }): string | null {
  const zone = info.object;
  if (!zone) return null;

  const typeLabel = zone.zone_type.charAt(0).toUpperCase() + zone.zone_type.slice(1);
  return `${zone.name}
Type: ${typeLabel}
Risk: ${zone.risk_level.toUpperCase()}
${zone.description}`;
}
