import React, { useEffect, useState } from 'react';
import { Badge, IconButton, Popover, Box, Typography } from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';
import { useUnreadCount } from '../hooks';
import { WebSocketManager } from '../../../lib/websocket';
import { useAuthStore } from '../../auth/store';

export function NotificationBell() {
  const { data: initialCount = 0 } = useUnreadCount();
  const [realtimeCount, setRealtimeCount] = useState(0);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  // Sincronizar el conteo inicial de la REST API
  useEffect(() => {
    setRealtimeCount(initialCount);
  }, [initialCount]);

  // Conexión WebSocket para tiempo real
  useEffect(() => {
    if (!isAuthenticated) return;

    // Conectar al endpoint ws/notifications/ dictado por el diseño
    const wsManager = new WebSocketManager('ws/notifications/');
    wsManager.connect();

    // Simulación de escucha de mensajes (deberás adaptarlo según cómo el backend envíe el JSON)
    const ws = wsManager['ws'] as WebSocket;
    const originalOnMessage = ws.onmessage;
    ws.onmessage = (event) => {
      if (originalOnMessage) originalOnMessage.call(ws, event);
      
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'new_notification') {
          setRealtimeCount((prev) => prev + 1);
        }
      } catch (e) {
        console.error("Error parseando notificación WS", e);
      }
    };

    return () => {
      wsManager.disconnect();
    };
  }, [isAuthenticated]);

  return (
    <IconButton color="inherit">
      <Badge badgeContent={realtimeCount} color="secondary">
        <NotificationsIcon />
      </Badge>
    </IconButton>
  );
}