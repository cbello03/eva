import { useAuthStore } from '../features/auth/store';

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private messageQueue: any[] = [];
  private pingInterval: NodeJS.Timeout | null = null;
  
  // Tiempos de backoff exponencial: 1s, 2s, 4s, 8s, 16s... (máximo 30s)
  private getBackoffTime() {
    const time = Math.pow(2, this.reconnectAttempts) * 1000;
    return Math.min(time, 30000); 
  }

  constructor(endpoint: string) {
    // endpoint debe ser algo como 'ws/notifications/' o 'ws/chat/1/'
    const baseUrl = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.url = `${baseUrl}//${host}/${endpoint}`;
  }

  public connect() {
    const token = useAuthStore.getState().accessToken;
    if (!token) {
      console.warn('Intento de conexión WebSocket sin token.');
      return;
    }

    // Autenticación vía query param requerida por el backend Django Channels
    const fullUrl = `${this.url}?token=${token}`;
    this.ws = new WebSocket(fullUrl);

    this.ws.onopen = () => {
      console.log(`Conectado a ${this.url}`);
      this.reconnectAttempts = 0;
      this.flushMessageQueue(); // Enviar mensajes encolados
      this.startPingPong();
    };

    this.ws.onmessage = (event) => {
      // Aquí despacharías eventos según tu arquitectura (ej. a Zustand o React Query)
      console.log('Mensaje recibido:', event.data);
    };

    this.ws.onclose = (event) => {
      this.stopPingPong();
      // Si no es un cierre limpio, intentar reconectar
      if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
        const backoff = this.getBackoffTime();
        console.log(`Reconectando en ${backoff / 1000}s...`);
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, backoff);
      }
    };

    this.ws.onerror = (error) => {
      console.error('Error en WebSocket:', error);
      // El evento onclose se disparará después de onerror
    };
  }

  public send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket no está abierto. Encolando mensaje...');
      this.messageQueue.push(data);
    }
  }

  private flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const msg = this.messageQueue.shift();
      this.send(msg);
    }
  }

  private startPingPong() {
    // Detección de conexión obsoleta cada 30 segundos
    this.pingInterval = setInterval(() => {
      this.send({ type: 'ping' });
    }, 30000);
  }

  private stopPingPong() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  public disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Desconexión intencional del cliente');
      this.ws = null;
    }
  }
}