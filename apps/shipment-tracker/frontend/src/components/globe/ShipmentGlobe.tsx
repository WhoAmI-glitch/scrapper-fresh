'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import { MapboxOverlay } from '@deck.gl/mapbox';
import type { ActiveShipment, RiskZone } from '@/lib/types';
import { createVesselLayer, getVesselTooltip } from './VesselLayer';
import { createRouteLayers } from './RouteLayer';
import { createRiskZoneLayer, getRiskZoneTooltip } from './RiskZoneLayer';

// ── Port markers ──────────────────────────────────────────────────────────────

interface PortPoint {
  id: string;
  name: string;
  lon: number;
  lat: number;
  kind: 'load' | 'discharge';
}

function derivePortPoints(shipments: ActiveShipment[]): PortPoint[] {
  const seen = new Set<string>();
  const ports: PortPoint[] = [];

  for (const s of shipments) {
    const loadKey = `${s.load_port_code}-load`;
    if (!seen.has(loadKey)) {
      seen.add(loadKey);
      ports.push({
        id: loadKey,
        name: s.load_port_name,
        lon: s.load_port_lon,
        lat: s.load_port_lat,
        kind: 'load',
      });
    }

    const dischargeKey = `${s.discharge_port_code}-discharge`;
    if (!seen.has(dischargeKey)) {
      seen.add(dischargeKey);
      ports.push({
        id: dischargeKey,
        name: s.discharge_port_name,
        lon: s.discharge_port_lon,
        lat: s.discharge_port_lat,
        kind: 'discharge',
      });
    }
  }

  return ports;
}

// ── Component ─────────────────────────────────────────────────────────────────

interface ShipmentGlobeProps {
  shipments: ActiveShipment[];
  riskZones: RiskZone[];
  selectedShipmentId: string | null;
  onSelectShipment: (id: string | null) => void;
}

/**
 * Main globe visualisation.
 *
 * Renders a Mapbox GL map in globe projection with dark styling, overlaying
 * deck.gl layers for vessels, routes, and risk zones.
 *
 * The globe auto-rotates slowly when idle; user interaction pauses rotation.
 */
export default function ShipmentGlobe({
  shipments,
  riskZones,
  selectedShipmentId,
  onSelectShipment,
}: ShipmentGlobeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const rotationFrameRef = useRef<number | null>(null);
  const isInteractingRef = useRef(false);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const tooltipRef = useRef<HTMLDivElement | null>(null);

  // Track whether the map is initialized
  const [mapReady, setMapReady] = useState(false);

  // ── Initialize Mapbox map ────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;

    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    if (!token) {
      console.error('NEXT_PUBLIC_MAPBOX_TOKEN is not set');
      return;
    }

    mapboxgl.accessToken = token;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [20, 10],
      zoom: 1.8,
      projection: 'globe',
      antialias: true,
    });

    mapRef.current = map;

    // Create tooltip div
    const tooltipEl = document.createElement('div');
    tooltipEl.className =
      'absolute pointer-events-none z-50 rounded-lg bg-slate-900/95 px-3 py-2 text-xs text-gray-200 shadow-xl border border-slate-700/50 whitespace-pre-line hidden max-w-xs';
    containerRef.current.appendChild(tooltipEl);
    tooltipRef.current = tooltipEl;

    // Globe atmosphere styling
    map.on('style.load', () => {
      map.setFog({
        color: 'rgb(10, 10, 20)',
        'high-color': 'rgb(20, 20, 50)',
        'horizon-blend': 0.08,
        'space-color': 'rgb(5, 5, 15)',
        'star-intensity': 0.6,
      });
    });

    // Create deck.gl overlay
    const overlay = new MapboxOverlay({
      interleaved: false,
      layers: [],
    });
    overlayRef.current = overlay;
    map.addControl(overlay as unknown as mapboxgl.IControl);

    // Navigation controls
    map.addControl(new mapboxgl.NavigationControl({ showCompass: true }), 'top-left');

    // Track user interaction to pause auto-rotation
    const startInteract = () => {
      isInteractingRef.current = true;
    };
    const endInteract = () => {
      // Resume auto-rotation after a brief delay
      setTimeout(() => {
        isInteractingRef.current = false;
      }, 3000);
    };

    map.on('mousedown', startInteract);
    map.on('touchstart', startInteract);
    map.on('mouseup', endInteract);
    map.on('touchend', endInteract);
    map.on('wheel', () => {
      startInteract();
      endInteract();
    });

    // Click on empty space deselects
    map.on('click', () => {
      // deck.gl click handler fires first for vessels; if nothing is picked,
      // the map click fires and we deselect
    });

    map.on('load', () => {
      setMapReady(true);
    });

    // Auto-rotation
    function rotateGlobe() {
      if (!isInteractingRef.current && mapRef.current) {
        const center = mapRef.current.getCenter();
        center.lng += 0.01; // slow rotation
        mapRef.current.setCenter(center);
      }
      rotationFrameRef.current = requestAnimationFrame(rotateGlobe);
    }
    rotationFrameRef.current = requestAnimationFrame(rotateGlobe);

    return () => {
      if (rotationFrameRef.current) {
        cancelAnimationFrame(rotationFrameRef.current);
      }
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
      tooltipEl.remove();
      map.remove();
      mapRef.current = null;
      overlayRef.current = null;
    };
  }, []);

  // ── Click-on-empty-space to deselect ────────────────────────────────────
  const onSelectRef = useRef(onSelectShipment);
  onSelectRef.current = onSelectShipment;

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    const handler = () => {
      // Small delay so deck.gl onClick fires first
      setTimeout(() => {
        // If deck.gl handled the click it will have called onSelectShipment already
      }, 50);
    };
    map.on('click', handler);
    return () => {
      map.off('click', handler);
    };
  }, [mapReady]);

  // ── Update deck.gl layers whenever data changes ─────────────────────────
  const updateLayers = useCallback(() => {
    if (!overlayRef.current) return;

    const vesselLayer = createVesselLayer({
      shipments,
      selectedShipmentId,
      onSelectShipment,
    });

    const routeLayer = createRouteLayers({
      shipments,
      selectedShipmentId,
    });

    const riskLayer = createRiskZoneLayer({ riskZones });

    overlayRef.current.setProps({
      layers: [riskLayer, routeLayer, vesselLayer],
      getTooltip: (info: { layer?: { id?: string }; object?: unknown }) => {
        if (!info.object) {
          if (tooltipRef.current) tooltipRef.current.classList.add('hidden');
          return null;
        }

        let text: string | null = null;
        if (info.layer?.id === 'vessel-layer') {
          text = getVesselTooltip(info as Parameters<typeof getVesselTooltip>[0]);
        } else if (info.layer?.id === 'risk-zone-layer') {
          text = getRiskZoneTooltip(info as Parameters<typeof getRiskZoneTooltip>[0]);
        }

        if (text && tooltipRef.current) {
          tooltipRef.current.textContent = text;
          tooltipRef.current.classList.remove('hidden');
        } else if (tooltipRef.current) {
          tooltipRef.current.classList.add('hidden');
        }

        return null; // We handle tooltip rendering ourselves
      },
    });
  }, [shipments, riskZones, selectedShipmentId, onSelectShipment]);

  useEffect(() => {
    if (mapReady) {
      updateLayers();
    }
  }, [mapReady, updateLayers]);

  // ── Port markers via Mapbox GL markers ──────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    // Remove old markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    const ports = derivePortPoints(shipments);

    for (const port of ports) {
      const el = document.createElement('div');
      el.className = 'port-marker';
      el.style.width = '8px';
      el.style.height = '8px';
      el.style.borderRadius = '50%';
      el.style.border = '1.5px solid rgba(255,255,255,0.8)';
      el.style.backgroundColor =
        port.kind === 'load' ? 'rgba(34, 197, 94, 0.9)' : 'rgba(147, 51, 234, 0.9)';
      el.style.cursor = 'pointer';
      el.title = port.name;

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([port.lon, port.lat])
        .addTo(map);

      markersRef.current.push(marker);
    }

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
    };
  }, [shipments, mapReady]);

  // ── Fly to selected vessel ──────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || !mapReady || !selectedShipmentId) return;

    const selected = shipments.find((s) => s.id === selectedShipmentId);
    if (selected?.vessel_lat != null && selected?.vessel_lon != null) {
      mapRef.current.flyTo({
        center: [selected.vessel_lon, selected.vessel_lat],
        zoom: 4,
        duration: 1500,
        essential: true,
      });
      // Pause rotation during fly-to
      isInteractingRef.current = true;
      setTimeout(() => {
        isInteractingRef.current = false;
      }, 5000);
    }
  }, [selectedShipmentId, shipments, mapReady]);

  // ── Custom cursor tracking for tooltip positioning ──────────────────────
  useEffect(() => {
    const container = containerRef.current;
    const tooltip = tooltipRef.current;
    if (!container || !tooltip) return;

    const handleMove = (e: MouseEvent) => {
      tooltip.style.left = `${e.offsetX + 12}px`;
      tooltip.style.top = `${e.offsetY + 12}px`;
    };

    container.addEventListener('mousemove', handleMove);
    return () => container.removeEventListener('mousemove', handleMove);
  }, []);

  return (
    <div ref={containerRef} className="absolute inset-0 h-full w-full">
      {/* Mapbox GL renders into this container */}
      {!mapReady && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-950">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-600 border-t-blue-500" />
            <span className="text-sm text-slate-400">Loading globe...</span>
          </div>
        </div>
      )}
    </div>
  );
}
