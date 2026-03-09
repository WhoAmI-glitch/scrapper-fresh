import type { WsMessage, WsVesselUpdate, WsNewAlert, WsShipmentUpdate } from './types';

type VesselUpdateCallback = (data: WsVesselUpdate['data']) => void;
type NewAlertCallback = (data: WsNewAlert['data']) => void;
type ShipmentUpdateCallback = (data: WsShipmentUpdate['data']) => void;

interface WebSocketClient {
  onVesselUpdate: (cb: VesselUpdateCallback) => () => void;
  onNewAlert: (cb: NewAlertCallback) => () => void;
  onShipmentUpdate: (cb: ShipmentUpdateCallback) => () => void;
  close: () => void;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/live';

// Max delay between reconnection attempts (30 seconds)
const MAX_RECONNECT_DELAY_MS = 30_000;
const BASE_RECONNECT_DELAY_MS = 1_000;

/**
 * Creates a reconnecting WebSocket connection to the backend.
 * Dispatches typed events for vessel updates, new alerts, and shipment updates.
 *
 * Returns an object with listener registration methods and a close() method.
 * Each listener registration returns an unsubscribe function.
 */
export function createWebSocket(): WebSocketClient {
  const vesselListeners = new Set<VesselUpdateCallback>();
  const alertListeners = new Set<NewAlertCallback>();
  const shipmentListeners = new Set<ShipmentUpdateCallback>();

  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  let intentionallyClosed = false;

  function connect() {
    if (intentionallyClosed) return;

    try {
      ws = new WebSocket(WS_URL);
    } catch {
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      // Reset backoff on successful connection
      reconnectAttempts = 0;
    };

    ws.onmessage = (event: MessageEvent) => {
      let message: WsMessage;
      try {
        message = JSON.parse(event.data as string) as WsMessage;
      } catch {
        // Ignore malformed messages
        return;
      }

      switch (message.type) {
        case 'vessel_update':
          vesselListeners.forEach((cb) => cb(message.data as WsVesselUpdate['data']));
          break;
        case 'new_alert':
          alertListeners.forEach((cb) => cb(message.data as WsNewAlert['data']));
          break;
        case 'shipment_update':
          shipmentListeners.forEach((cb) => cb(message.data as WsShipmentUpdate['data']));
          break;
      }
    };

    ws.onclose = () => {
      ws = null;
      if (!intentionallyClosed) {
        scheduleReconnect();
      }
    };

    ws.onerror = () => {
      // onclose will fire after onerror, which will trigger reconnection
      ws?.close();
    };
  }

  function scheduleReconnect() {
    if (intentionallyClosed) return;

    const delay = Math.min(
      BASE_RECONNECT_DELAY_MS * Math.pow(2, reconnectAttempts),
      MAX_RECONNECT_DELAY_MS,
    );
    reconnectAttempts += 1;

    reconnectTimeout = setTimeout(() => {
      reconnectTimeout = null;
      connect();
    }, delay);
  }

  // Start the initial connection
  connect();

  return {
    onVesselUpdate(cb: VesselUpdateCallback) {
      vesselListeners.add(cb);
      return () => {
        vesselListeners.delete(cb);
      };
    },

    onNewAlert(cb: NewAlertCallback) {
      alertListeners.add(cb);
      return () => {
        alertListeners.delete(cb);
      };
    },

    onShipmentUpdate(cb: ShipmentUpdateCallback) {
      shipmentListeners.add(cb);
      return () => {
        shipmentListeners.delete(cb);
      };
    },

    close() {
      intentionallyClosed = true;
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
      }
      ws?.close();
      ws = null;
      vesselListeners.clear();
      alertListeners.clear();
      shipmentListeners.clear();
    },
  };
}
