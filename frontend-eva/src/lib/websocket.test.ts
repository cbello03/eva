import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { WebSocketManager, type WebSocketStatus } from "./websocket";

// ── Mock WebSocket ───────────────────────────────────────────────────

type WSHandler = ((event: unknown) => void) | null;

class MockWebSocket {
  static CONNECTING = 0 as const;
  static OPEN = 1 as const;
  static CLOSING = 2 as const;
  static CLOSED = 3 as const;

  CONNECTING = 0 as const;
  OPEN = 1 as const;
  CLOSING = 2 as const;
  CLOSED = 3 as const;

  readyState: number = MockWebSocket.CONNECTING;
  url: string;
  onopen: WSHandler = null;
  onmessage: WSHandler = null;
  onclose: WSHandler = null;
  onerror: WSHandler = null;
  sentMessages: string[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  send(data: string): void {
    this.sentMessages.push(data);
  }

  close(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ code: 1000, reason: "" });
  }

  // Test helpers
  simulateOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.({});
  }

  simulateMessage(data: unknown): void {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent);
  }

  simulateClose(code = 1006, reason = ""): void {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ code, reason } as CloseEvent);
  }

  simulateError(): void {
    this.onerror?.({});
  }

  static instances: MockWebSocket[] = [];
  static reset(): void {
    MockWebSocket.instances = [];
  }
  static latest(): MockWebSocket {
    return MockWebSocket.instances[MockWebSocket.instances.length - 1]!;
  }
}

// ── Setup ────────────────────────────────────────────────────────────

const TOKEN = "test-jwt-token";
const ENDPOINT = "/ws/chat/1/";

function createManager(
  opts?: ConstructorParameters<typeof WebSocketManager>[2],
): WebSocketManager {
  return new WebSocketManager(ENDPOINT, () => TOKEN, opts);
}

beforeEach(() => {
  vi.useFakeTimers();
  MockWebSocket.reset();
  vi.stubGlobal("WebSocket", MockWebSocket);
  // Mock window.location for URL construction
  vi.stubGlobal("location", {
    protocol: "https:",
    host: "eva.test",
  });
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

// ── Tests ────────────────────────────────────────────────────────────

describe("WebSocketManager", () => {
  describe("connection", () => {
    it("connects with JWT token as query param", () => {
      const ws = createManager();
      ws.connect();

      const mock = MockWebSocket.latest();
      expect(mock.url).toBe(
        `wss://eva.test${ENDPOINT}?token=${encodeURIComponent(TOKEN)}`,
      );
    });

    it("uses ws: protocol for http origins", () => {
      vi.stubGlobal("location", { protocol: "http:", host: "localhost:3000" });
      const ws = createManager();
      ws.connect();

      const mock = MockWebSocket.latest();
      expect(mock.url.startsWith("ws://localhost:3000")).toBe(true);
    });

    it("transitions to connected on open", () => {
      const ws = createManager();
      const statuses: WebSocketStatus[] = [];
      ws.onStatusChange((s) => statuses.push(s));

      ws.connect();
      MockWebSocket.latest().simulateOpen();

      expect(ws.getStatus()).toBe("connected");
      expect(statuses).toContain("connecting");
      expect(statuses).toContain("connected");
    });

    it("does not connect without a token", () => {
      const ws = new WebSocketManager(ENDPOINT, () => null);
      ws.connect();

      expect(MockWebSocket.instances).toHaveLength(0);
      expect(ws.getStatus()).toBe("disconnected");
    });

    it("is a no-op if already connected", () => {
      const ws = createManager();
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      ws.connect(); // second call
      expect(MockWebSocket.instances).toHaveLength(1);
    });
  });

  describe("messaging", () => {
    it("sends JSON messages when connected", () => {
      const ws = createManager();
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      ws.send({ type: "chat", content: "hello" });

      const mock = MockWebSocket.latest();
      expect(mock.sentMessages).toHaveLength(1);
      expect(JSON.parse(mock.sentMessages[0]!)).toEqual({
        type: "chat",
        content: "hello",
      });
    });

    it("delivers parsed messages to handlers", () => {
      const ws = createManager();
      const received: unknown[] = [];
      ws.onMessage((data) => received.push(data));

      ws.connect();
      MockWebSocket.latest().simulateOpen();
      MockWebSocket.latest().simulateMessage({ type: "chat", text: "hi" });

      expect(received).toHaveLength(1);
      expect(received[0]).toEqual({ type: "chat", text: "hi" });
    });

    it("supports unsubscribing message handlers", () => {
      const ws = createManager();
      const received: unknown[] = [];
      const unsub = ws.onMessage((data) => received.push(data));

      ws.connect();
      MockWebSocket.latest().simulateOpen();

      MockWebSocket.latest().simulateMessage({ n: 1 });
      unsub();
      MockWebSocket.latest().simulateMessage({ n: 2 });

      expect(received).toHaveLength(1);
    });
  });

  describe("message queue", () => {
    it("queues messages when disconnected and flushes on reconnect", () => {
      const ws = createManager();
      ws.connect();
      // Don't open yet — still connecting

      ws.send({ queued: 1 });
      ws.send({ queued: 2 });

      // Now open
      MockWebSocket.latest().simulateOpen();

      const mock = MockWebSocket.latest();
      // The ping message may also be sent, so check the first two
      expect(mock.sentMessages.length).toBeGreaterThanOrEqual(2);
      expect(JSON.parse(mock.sentMessages[0]!)).toEqual({ queued: 1 });
      expect(JSON.parse(mock.sentMessages[1]!)).toEqual({ queued: 2 });
    });

    it("flushes queued messages after reconnection", () => {
      const ws = createManager({
        initialReconnectDelay: 100,
      });
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      // Simulate disconnect
      MockWebSocket.latest().simulateClose();

      // Queue a message while disconnected
      ws.send({ afterDisconnect: true });

      // Advance timer to trigger reconnect
      vi.advanceTimersByTime(100);

      // New connection opens
      MockWebSocket.latest().simulateOpen();

      const mock = MockWebSocket.latest();
      expect(mock.sentMessages[0]).toBe(
        JSON.stringify({ afterDisconnect: true }),
      );
    });
  });

  describe("reconnection with exponential backoff", () => {
    it("reconnects with exponential backoff: 1s, 2s, 4s, 8s", () => {
      const ws = createManager({ initialReconnectDelay: 1000 });
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      // First disconnect → 1s delay
      MockWebSocket.latest().simulateClose();
      expect(ws.getStatus()).toBe("reconnecting");

      vi.advanceTimersByTime(999);
      expect(MockWebSocket.instances).toHaveLength(1); // not yet
      vi.advanceTimersByTime(1);
      expect(MockWebSocket.instances).toHaveLength(2); // reconnected at 1s

      // Second disconnect → 2s delay
      MockWebSocket.latest().simulateClose();
      vi.advanceTimersByTime(2000);
      expect(MockWebSocket.instances).toHaveLength(3);

      // Third disconnect → 4s delay
      MockWebSocket.latest().simulateClose();
      vi.advanceTimersByTime(4000);
      expect(MockWebSocket.instances).toHaveLength(4);

      // Fourth disconnect → 8s delay
      MockWebSocket.latest().simulateClose();
      vi.advanceTimersByTime(8000);
      expect(MockWebSocket.instances).toHaveLength(5);
    });

    it("caps reconnect delay at maxReconnectDelay", () => {
      const ws = createManager({
        initialReconnectDelay: 1000,
        maxReconnectDelay: 4000,
      });
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      // Disconnect 5 times — delay should cap at 4s
      for (let i = 0; i < 5; i++) {
        MockWebSocket.latest().simulateClose();
        vi.advanceTimersByTime(4000);
      }

      // All reconnects should have happened within 4s each
      // 1 initial + 5 reconnects = 6
      expect(MockWebSocket.instances).toHaveLength(6);
    });

    it("resets reconnect attempts on successful connection", () => {
      const ws = createManager({ initialReconnectDelay: 1000 });
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      // Disconnect and reconnect
      MockWebSocket.latest().simulateClose();
      vi.advanceTimersByTime(1000);
      MockWebSocket.latest().simulateOpen(); // successful reconnect

      // Next disconnect should use initial delay (1s), not 2s
      MockWebSocket.latest().simulateClose();
      vi.advanceTimersByTime(999);
      expect(MockWebSocket.instances).toHaveLength(2); // not yet
      vi.advanceTimersByTime(1);
      expect(MockWebSocket.instances).toHaveLength(3); // at 1s
    });

    it("does not reconnect on auth rejection (4001, 4003)", () => {
      const ws = createManager();
      ws.connect();
      MockWebSocket.latest().simulateClose(4001, "Unauthorized");

      vi.advanceTimersByTime(60000);
      expect(MockWebSocket.instances).toHaveLength(1);
      expect(ws.getStatus()).toBe("disconnected");
    });

    it("respects maxReconnectAttempts", () => {
      const ws = createManager({
        initialReconnectDelay: 100,
        maxReconnectAttempts: 2,
      });
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      // First disconnect → attempt 1
      MockWebSocket.latest().simulateClose();
      vi.advanceTimersByTime(100);
      expect(MockWebSocket.instances).toHaveLength(2);

      // Second disconnect → attempt 2
      MockWebSocket.latest().simulateClose();
      vi.advanceTimersByTime(200);
      expect(MockWebSocket.instances).toHaveLength(3);

      // Third disconnect → max reached, no more attempts
      MockWebSocket.latest().simulateClose();
      vi.advanceTimersByTime(60000);
      expect(MockWebSocket.instances).toHaveLength(3);
      expect(ws.getStatus()).toBe("disconnected");
    });
  });

  describe("ping/pong stale connection detection", () => {
    it("sends ping at configured interval", () => {
      const ws = createManager({ pingInterval: 5000 });
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      vi.advanceTimersByTime(5000);

      const mock = MockWebSocket.latest();
      const pings = mock.sentMessages.filter(
        (m) => JSON.parse(m).type === "ping",
      );
      expect(pings).toHaveLength(1);
    });

    it("closes connection when pong is not received within timeout", () => {
      const ws = createManager({
        pingInterval: 5000,
        pongTimeout: 2000,
      });
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      // Trigger ping
      vi.advanceTimersByTime(5000);

      // Wait for pong timeout without sending pong
      vi.advanceTimersByTime(2000);

      expect(MockWebSocket.latest().readyState).toBe(MockWebSocket.CLOSED);
    });

    it("does not close connection when pong is received in time", () => {
      const ws = createManager({
        pingInterval: 5000,
        pongTimeout: 2000,
      });
      ws.connect();
      const mock = MockWebSocket.latest();
      mock.simulateOpen();

      // Trigger ping
      vi.advanceTimersByTime(5000);

      // Respond with pong
      mock.simulateMessage({ type: "pong" });

      // Wait past pong timeout
      vi.advanceTimersByTime(3000);

      expect(mock.readyState).toBe(MockWebSocket.OPEN);
    });

    it("does not forward pong messages to handlers", () => {
      const ws = createManager({ pingInterval: 5000 });
      const received: unknown[] = [];
      ws.onMessage((data) => received.push(data));

      ws.connect();
      MockWebSocket.latest().simulateOpen();

      vi.advanceTimersByTime(5000);
      MockWebSocket.latest().simulateMessage({ type: "pong" });

      expect(received).toHaveLength(0);
    });
  });

  describe("disconnect", () => {
    it("stops reconnection on intentional disconnect", () => {
      const ws = createManager({ initialReconnectDelay: 100 });
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      ws.disconnect();

      vi.advanceTimersByTime(60000);
      expect(MockWebSocket.instances).toHaveLength(1);
      expect(ws.getStatus()).toBe("disconnected");
    });

    it("clears ping interval on disconnect", () => {
      const ws = createManager({ pingInterval: 5000 });
      ws.connect();
      MockWebSocket.latest().simulateOpen();

      ws.disconnect();

      // No pings should be sent after disconnect
      vi.advanceTimersByTime(10000);
      // Only 1 instance, and it was closed
      expect(MockWebSocket.latest().readyState).toBe(MockWebSocket.CLOSED);
    });
  });
});
