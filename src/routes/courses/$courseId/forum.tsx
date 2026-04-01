import React, { useState } from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { Box, Typography, Button, CircularProgress, Card, CardContent, TextField, Divider, Avatar } from '@mui/material';
import ForumIcon from '@mui/icons-material/Forum';
import { useThreads, useCreateThread } from '../../../features/social/hooks';

export const Route = createFileRoute('/courses/$courseId/forum')({
  component: CourseForum,
});

function CourseForum() {
  const { courseId } = Route.useParams();
  const { data: threads, isLoading } = useThreads(courseId);
  const createThreadMutation = useCreateThread(courseId);
  
  const [showForm, setShowForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newBody, setNewBody] = useState('');

  const handleCreateThread = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newBody.trim()) return;

    createThreadMutation.mutate({ title: newTitle, body: newBody }, {
      onSuccess: () => {
        setShowForm(false);
        setNewTitle('');
        setNewBody('');
      }
    });
  };

  return (
    <Box sx={{ mt: 4, maxWidth: 800, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <ForumIcon fontSize="large" color="primary" />
          Foro de Discusión
        </Typography>
        <Button 
          variant="contained" 
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancelar' : 'Nueva Pregunta'}
        </Button>
      </Box>

      {/* Formulario para nuevo hilo */}
      {showForm && (
        <Card sx={{ mb: 4, bgcolor: '#f8f9fa' }}>
          <CardContent component="form" onSubmit={handleCreateThread}>
            <Typography variant="h6" gutterBottom>Iniciar nueva discusión</Typography>
            <TextField
              fullWidth
              label="Título de tu pregunta"
              variant="outlined"
              margin="normal"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              disabled={createThreadMutation.isPending}
            />
            <TextField
              fullWidth
              label="Detalla tu duda o comentario"
              variant="outlined"
              margin="normal"
              multiline
              rows={4}
              value={newBody}
              onChange={(e) => setNewBody(e.target.value)}
              disabled={createThreadMutation.isPending}
            />
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button 
                type="submit" 
                variant="contained" 
                disabled={!newTitle.trim() || !newBody.trim() || createThreadMutation.isPending}
              >
                {createThreadMutation.isPending ? 'Publicando...' : 'Publicar'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Lista de Hilos */}
      {isLoading ? (
        <Box display="flex" justifyContent="center" mt={4}><CircularProgress /></Box>
      ) : !threads?.length ? (
        <Typography color="text.secondary" textAlign="center" mt={4}>
          Aún no hay discusiones en este curso. ¡Sé el primero en preguntar!
        </Typography>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {threads.map((thread) => (
            <Card key={thread.id} sx={{ '&:hover': { boxShadow: 3 } }}>
              <CardContent sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                <Avatar sx={{ bgcolor: 'secondary.main' }}>
                  {thread.author_name.charAt(0).toUpperCase()}
                </Avatar>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" color="primary" sx={{ cursor: 'pointer' }}>
                    {thread.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Por {thread.author_name} • {new Date(thread.created_at).toLocaleDateString()}
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center', minWidth: 80 }}>
                  <Typography variant="h6">{thread.replies_count}</Typography>
                  <Typography variant="caption" color="text.secondary">respuestas</Typography>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
}