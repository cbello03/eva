type MessageHandler = (data: unknown) => void

interface QueuedMessage {
  data: string
  timestamp: number
}

/**
 * WebSocket connection manager with:
 * - Automatic reconnection using exponential backoff (1s → 30s cap)
 * - Message queue for messages sent while disconnected
 * - Stale-connection detection via ping/pong (30 s interval)
 */
export class WebSocketManager {
  private ws: WebSocket | null = null
  private url: string
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private messageQueue: QueuedMessage[] = []

  // Reconnection state
  private reconnectAttempts = 0
  private readonly maxReconnectDelay = 30_000 // 30 s
  private readonly baseReconnectDelay = 1_000 // 1 s
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private intentionallyClosed = false

  // Ping / pong keep-alive
  private readonly pingInterval = 30_000 // 30 s
  private pingTimer: ReturnType<typeof setInterval> | null = null
  private pongReceived = true

  constructor(url: string) {
    this.url = url
  }

  // -----------------------------------------------------------------------
  // Public API
  // -----------------------------------------------------------------------

  /** Open the WebSocket connection. */
  connect(): void {
    this.intentionallyClosed = false
    this.createConnection()
  }

  /** Gracefully close the connection (no auto-reconnect). */
  disconnect(): void {
    this.intentionallyClosed = true
    this.clearTimers()
    this.ws?.close()
    this.ws = null
  }

  /** Send a JSON-serialisable message. Queues if not connected. */
  send(event: string, payload: unknown): void {
    const message = JSON.stringify({ event, payload })

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message)
    } else {
      this.messageQueue.push({ data: message, timestamp: Date.now() })
    }
  }

  /** Subscribe to a named event. Returns an unsubscribe function. */
  on(event: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set())
    }
    this.handlers.get(event)!.add(handler)

    return () => {
      this.handlers.get(event)?.delete(handler)
    }
  }

  /** Current connection state. */
  get connected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  // -----------------------------------------------------------------------
  // Internal helpers
  // -----------------------------------------------------------------------

  private createConnection(): void {
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this.flushQueue()
      this.startPingPong()
    }

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const parsed = JSON.parse(event.data as string) as {
          event?: string
          payload?: unknown
        }

        // Handle pong responses for keep-alive
        if (parsed.event === 'pong') {
          this.pongReceived = true
          return
        }

        if (parsed.event) {
          const handlers = this.handlers.get(parsed.event)
          handlers?.forEach((handler) => handler(parsed.payload))
        }
      } catch {
        // Non-JSON message — ignore
      }
    }

    this.ws.onclose = () => {
      this.stopPingPong()
      if (!this.intentionallyClosed) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = () => {
      // The browser fires `onclose` after `onerror`, so reconnection
      // is handled there. Nothing extra needed here.
    }
  }

  /** Exponential backoff: 1 s, 2 s, 4 s, 8 s, … capped at 30 s. */
  private getReconnectDelay(): number {
    const delay = this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts)
    return Math.min(delay, this.maxReconnectDelay)
  }

  private scheduleReconnect(): void {
    const delay = this.getReconnectDelay()
    this.reconnectAttempts++
    this.reconnectTimer = setTimeout(() => this.createConnection(), delay)
  }

  /** Flush any messages that were queued while disconnected. */
  private flushQueue(): void {
    while (this.messageQueue.length > 0) {
      const msg = this.messageQueue.shift()!
      this.ws?.send(msg.data)
    }
  }

  // -----------------------------------------------------------------------
  // Ping / pong keep-alive
  // -----------------------------------------------------------------------

  private startPingPong(): void {
    this.stopPingPong()
    this.pongReceived = true

    this.pingTimer = setInterval(() => {
      if (!this.pongReceived) {
        // Server didn't respond — connection is stale, force reconnect
        this.ws?.close()
        return
      }
      this.pongReceived = false
      this.ws?.send(JSON.stringify({ event: 'ping' }))
    }, this.pingInterval)
  }

  private stopPingPong(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
  }

  private clearTimers(): void {
    this.stopPingPong()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}
