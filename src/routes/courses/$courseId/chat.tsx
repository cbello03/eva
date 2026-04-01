import React, { useEffect, useState, useRef } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Box, Typography, TextField, IconButton, Paper, Avatar, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { useChatHistory } from '../../../features/social/hooks';
import { ChatMessage } from '../../../features/social/api';
import { WebSocketManager } from '../../../lib/websocket';
import { useUser } from '../../../features/auth/hooks';

export const Route = createFileRoute('/courses/$courseId/chat')({
  component: CourseChat,
});

function CourseChat() {
  const { courseId } = Route.useParams();
  const { data: currentUser } = useUser();
  const { data: history, isLoading } = useChatHistory(courseId);
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const wsManagerRef = useRef<WebSocketManager | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Cargar el historial en el estado local cuando la API responda
  useEffect(() => {
    if (history) setMessages(history);
  }, [history]);

  // Hacer scroll automático hacia abajo cuando llega un mensaje nuevo
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Conectar al WebSocket del curso
  useEffect(() => {
    // Endpoint dinámico: ej. ws/chat/1/
    wsManagerRef.current = new WebSocketManager(`ws/chat/${courseId}/`);
    wsManagerRef.current.connect();

    // Sobrescribimos el onmessage para capturar los eventos en vivo
    const ws = wsManagerRef.current['ws'] as WebSocket;
    const originalOnMessage = ws.onmessage;
    ws.onmessage = (event) => {
      if (originalOnMessage) originalOnMessage.call(ws, event);
      
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'chat_message') {
          setMessages((prev) => [...prev, data.payload]);
        }
      } catch (e) {
        console.error("Error procesando mensaje de chat", e);
      }
    };

    return () => {
      wsManagerRef.current?.disconnect();
    };
  }, [courseId]);

  const handleSendMessage = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim()) return;

    // 1. Enviamos el mensaje al servidor vía WebSocket
    wsManagerRef.current?.send({
      type: 'chat_message',
      payload: { body: inputValue.trim() }
    });

    // 2. Optimistic UI: Lo agregamos inmediatamente a nuestra pantalla 
    // (En un entorno real, esperaríamos el eco del servidor, pero para que sea fluido hacemos esto)
    const optimisticMessage: ChatMessage = {
      id: Date.now().toString(),
      author_name: currentUser?.display_name || 'Yo',
      body: inputValue.trim(),
      created_at: new Date().toISOString(),
      is_current_user: true
    };
    
    setMessages((prev) => [...prev, optimisticMessage]);
    setInputValue('');
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', mt: 4, height: '75vh', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h4" gutterBottom>
        Sala de Chat en Vivo
      </Typography>

      {/* Contenedor de Mensajes */}
      <Paper sx={{ flexGrow: 1, p: 2, mb: 2, overflowY: 'auto', bgcolor: '#f5f7fa' }}>
        {isLoading ? (
          <Box display="flex" justifyContent="center" mt={4}><CircularProgress /></Box>
        ) : !messages.length ? (
          <Typography color="text.secondary" textAlign="center" mt={4}>
            No hay mensajes aún. ¡Di hola!
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {messages.map((msg) => {
              const isMe = msg.is_current_user || msg.author_name === currentUser?.display_name;
              return (
                <Box key={msg.id} sx={{ display: 'flex', justifyContent: isMe ? 'flex-end' : 'flex-start' }}>
                  {!isMe && (
                    <Avatar sx={{ width: 32, height: 32, mr: 1, bgcolor: 'primary.main', fontSize: '0.875rem' }}>
                      {msg.author_name.charAt(0)}
                    </Avatar>
                  )}
                  <Box>
                    {!isMe && <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>{msg.author_name}</Typography>}
                    <Paper 
                      sx={{ 
                        p: 1.5, 
                        px: 2,
                        bgcolor: isMe ? 'primary.main' : 'white', 
                        color: isMe ? 'white' : 'text.primary',
                        borderRadius: isMe ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                        maxWidth: 400
                      }}
                    >
                      <Typography variant="body1">{msg.body}</Typography>
                    </Paper>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: isMe ? 'right' : 'left', mt: 0.5, px: 1 }}>
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </Typography>
                  </Box>
                </Box>
              );
            })}
            {/* Ancla invisible para el scroll automático */}
            <div ref={messagesEndRef} />
          </Box>
        )}
      </Paper>

      {/* Input de Mensaje */}
      <Box component="form" onSubmit={handleSendMessage} sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Escribe un mensaje..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          autoComplete="off"
        />
        <IconButton 
          color="primary" 
          type="submit" 
          disabled={!inputValue.trim()}
          sx={{ bgcolor: 'primary.light', color: 'white', '&:hover': { bgcolor: 'primary.main' }, borderRadius: 2, px: 3 }}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Box>
  );
}