import React, { useEffect, useState, useRef } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Box, Typography, TextField, CircularProgress, Paper, AvatarGroup, Avatar } from '@mui/material';
import { useWorkspace } from '../../features/collaboration/hooks';
import { WebSocketManager } from '../../lib/websocket';

export const Route = createFileRoute('/collaboration/$workspaceId')({
  component: CollabWorkspace,
});

function CollabWorkspace() {
  const { workspaceId } = Route.useParams();
  const { data: workspace, isLoading } = useWorkspace(workspaceId);
  
  const [content, setContent] = useState('');
  const [activeUsers, setActiveUsers] = useState<string[]>([]);
  const wsManagerRef = useRef<WebSocketManager | null>(null);

  // Cargar el documento inicial
  useEffect(() => {
    if (workspace) setContent(workspace.content);
  }, [workspace]);

  // Conectar al canal WebSocket del espacio de trabajo
  useEffect(() => {
    wsManagerRef.current = new WebSocketManager(`ws/collaboration/${workspaceId}/`);
    wsManagerRef.current.connect();

    const ws = wsManagerRef.current['ws'] as WebSocket;
    const originalOnMessage = ws.onmessage;
    ws.onmessage = (event) => {
      if (originalOnMessage) originalOnMessage.call(ws, event);
      
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'doc_update') {
          // Otro usuario escribió algo, actualizamos nuestro lienzo
          setContent(data.payload.content);
        } else if (data.type === 'user_joined') {
          // Alguien entró a la sala
          setActiveUsers((prev) => [...new Set([...prev, data.payload.user])]);
        }
      } catch (e) {
        console.error("Error procesando actualización del documento", e);
      }
    };

    return () => {
      wsManagerRef.current?.disconnect();
    };
  }, [workspaceId]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setContent(newContent); // Actualizamos nuestra pantalla
    
    // Transmitimos el cambio al servidor y a los demás compañeros
    wsManagerRef.current?.send({
      type: 'doc_update',
      payload: { content: newContent }
    });
  };

  if (isLoading) return <Box display="flex" justifyContent="center" mt={10}><CircularProgress /></Box>;

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto', mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">{workspace?.name || 'Espacio Colaborativo'}</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">En línea:</Typography>
          <AvatarGroup max={4}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>Yo</Avatar>
            {activeUsers.map(user => (
              <Avatar key={user} sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>{user.charAt(0)}</Avatar>
            ))}
          </AvatarGroup>
        </Box>
      </Box>

      <Paper elevation={3} sx={{ p: 2, minHeight: '65vh', bgcolor: '#fff', borderTop: '4px solid #1976d2' }}>
        <TextField
          fullWidth
          multiline
          minRows={20}
          variant="standard"
          InputProps={{ disableUnderline: true, style: { fontSize: '1.1rem', lineHeight: 1.6, fontFamily: 'monospace' } }}
          value={content}
          onChange={handleChange}
          placeholder="Comienza a escribir aquí..."
        />
      </Paper>
    </Box>
  );
}