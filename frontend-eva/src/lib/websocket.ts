/**
 * WebSocket connection manager with JWT auth, automatic reconnection,
 * message queuing, and stale connection detection.
 *
 * Supports multiple endpoint types: chat, notifications, collaboration.
 *
 * @example
 * ```ts
 * const ws = new WebSocketManager('/ws/chat/1/', () => useAuthStore.getState().accessToken);
 * ws.onMessage((data) => console.log(data));
 * ws.connect();
 * ```
 */

export type WebSocketStatus =
  | "connecting"
  | "connected"
  | "disconnected"
  | "reconnecting";

export type MessageHandler = (data: unknown) => void;
export type StatusHandler = (status: WebSocketStatus) => void;

interface WebSocketManagerOptions {
  /** Initial reconnect delay in ms (default: 1000) */
  initialReconnectDelay?: number;
  /** Maximum reconnect delay in ms (default: 30000) */
  maxReconnectDelay?: number;
  /** Ping interval in ms for stale connection detection (default: 30000) */
  pingInterval?: number;
  /** Time to wait for pong response before considering connection stale (default: 5000) */
  pongTimeout?: number;
  /** Maximum number of reconnect attempts before giving up (default: Infinity) */
  maxReconnectAttempts?: number;
}

const DEFAULT_OPTIONS: Required<WebSocketManagerOptions> = {
  initialReconnectDelay: 1000,
  maxReconnectDelay: 30000,
  pingInterval: 30000,
  pongTimeout: 5000,
  maxReconnectAttempts: Infinity,
};

export class WebSocketManager {
  private socket: WebSocket | null = null;
  private status: WebSocketStatus = "disconnected";
  private messageHandlers: Set<MessageHandler> = new Set();
  private statusHandlers: Set<StatusHandler> = new Set();
  private messageQueue: string[] = [];
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private pongTimer: ReturnType<typeof setTimeout> | null = null;
  private awaitingPong = false;
  private intentionallyClosed = false;
  private readonly options: Required<WebSocketManagerOptions>;
  private readonly endpoint: string;
  private readonly getToken: () => string | null;

  constructor(
    endpoint: string,
    getToken: () => string | null,
    options?: WebSocketManagerOptions,
  ) {
    this.endpoint = endpoint;
    this.getToken = getToken;
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  /** Current connection status. */
  getStatus(): WebSocketStatus {
    return this.status;
  }

  /** Register a handler for incoming messages. Returns an unsubscribe function. */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => {
      this.messageHandlers.delete(handler);
    };
  }

  /** Register a handler for status changes. Returns an unsubscribe function. */
  onStatusChange(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    return () => {
      this.statusHandlers.delete(handler);
    };
  }

  /** Open the WebSocket connection. */
  connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    this.intentionallyClosed = false;
    this.createConnection();
  }

  /** Close the connection and stop reconnection attempts. */
  disconnect(): void {
    this.intentionallyClosed = true;
    this.cleanup();
    this.setStatus("disconnected");
  }

  /** Send a message. Queues if not currently connected. */
  send(data: unknown): void {
    const message = JSON.stringify(data);

    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(message);
    } else {
      this.messageQueue.push(message);
    }
  }

  // ── Private methods ────────────────────────────────────────────────

  private createConnection(): void {
    this.cleanup();

    const token = this.getToken();
    if (!token) {
      console.warn("[WebSocket] No auth token available, cannot connect.");
      this.setStatus("disconnected");
      return;
    }

    const backendOrigin = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const parsed = new URL(backendOrigin);
    const protocol = parsed.protocol === "https:" ? "wss:" : "ws:";
    const host = parsed.host;
    const url = `${protocol}//${host}${this.endpoint}?token=${encodeURIComponent(token)}`;

    this.setStatus(
      this.reconnectAttempts > 0 ? "reconnecting" : "connecting",
    );

    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.setStatus("connected");
      this.flushMessageQueue();
      this.startPingInterval();
    };

    this.socket.onmessage = (event: MessageEvent) => {
      this.handleMessage(event);
    };

    this.socket.onclose = (event: CloseEvent) => {
      this.stopPingInterval();

      if (this.intentionallyClosed) {
        this.setStatus("disconnected");
        return;
      }

      // Auth failure — don't reconnect
      if (event.code === 4001 || event.code === 4003) {
        console.warn(
          `[WebSocket] Auth rejected (code ${event.code}), not reconnecting.`,
        );
        this.setStatus("disconnected");
        return;
      }

      this.scheduleReconnect();
    };

    this.socket.onerror = () => {
      // The onclose handler will fire after onerror, so reconnection
      // is handled there. We just log here.
      console.error("[WebSocket] Connection error on", this.endpoint);
    };
  }

  private handleMessage(event: MessageEvent): void {
    let data: unknown;
    try {
      data = JSON.parse(event.data as string);
    } catch {
      data = event.data;
    }

    // Handle pong responses for stale connection detection
    if (
      typeof data === "object" &&
      data !== null &&
      "type" in data &&
      (data as { type: string }).type === "pong"
    ) {
      this.awaitingPong = false;
      if (this.pongTimer) {
        clearTimeout(this.pongTimer);
        this.pongTimer = null;
      }
      return;
    }

    for (const handler of this.messageHandlers) {
      try {
        handler(data);
      } catch (err) {
        console.error("[WebSocket] Message handler error:", err);
      }
    }
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()!;
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send(message);
      } else {
        // Put it back and stop flushing — connection lost during flush
        this.messageQueue.unshift(message);
        break;
      }
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.warn("[WebSocket] Max reconnect attempts reached.");
      this.setStatus("disconnected");
      return;
    }

    const delay = Math.min(
      this.options.initialReconnectDelay *
        Math.pow(2, this.reconnectAttempts),
      this.options.maxReconnectDelay,
    );

    this.setStatus("reconnecting");
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      this.createConnection();
    }, delay);
  }

  private startPingInterval(): void {
    this.stopPingInterval();

    this.pingTimer = setInterval(() => {
      if (this.socket?.readyState !== WebSocket.OPEN) {
        return;
      }

      if (this.awaitingPong) {
        // Previous ping never got a pong — connection is stale
        console.warn("[WebSocket] Stale connection detected, reconnecting.");
        this.socket.close();
        return;
      }

      this.awaitingPong = true;
      this.socket.send(JSON.stringify({ type: "ping" }));

      this.pongTimer = setTimeout(() => {
        if (this.awaitingPong) {
          console.warn("[WebSocket] Pong timeout, closing stale connection.");
          this.socket?.close();
        }
      }, this.options.pongTimeout);
    }, this.options.pingInterval);
  }

  private stopPingInterval(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
    if (this.pongTimer) {
      clearTimeout(this.pongTimer);
      this.pongTimer = null;
    }
    this.awaitingPong = false;
  }

  private cleanup(): void {
    this.stopPingInterval();

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.socket) {
      // Remove handlers before closing to avoid triggering reconnect
      this.socket.onopen = null;
      this.socket.onmessage = null;
      this.socket.onclose = null;
      this.socket.onerror = null;

      if (
        this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING
      ) {
        this.socket.close();
      }
      this.socket = null;
    }
  }

  private setStatus(newStatus: WebSocketStatus): void {
    if (this.status === newStatus) return;
    this.status = newStatus;
    for (const handler of this.statusHandlers) {
      try {
        handler(newStatus);
      } catch (err) {
        console.error("[WebSocket] Status handler error:", err);
      }
    }
  }
}
