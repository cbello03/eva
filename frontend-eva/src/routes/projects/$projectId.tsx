import React, { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Box, Typography, Button, CircularProgress, Card, CardContent, Alert, Divider } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useProject, useSubmission, useSubmitProject } from '../../features/projects/hooks';

export const Route = createFileRoute('/projects/$projectId')({
  component: ProjectDetail,
});

function ProjectDetail() {
  const { projectId } = Route.useParams();
  const { data: project, isLoading: loadingProject } = useProject(projectId);
  const { data: submission, isLoading: loadingSubmission } = useSubmission(projectId);
  const submitMutation = useSubmitProject(projectId);
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg('');
    const file = e.target.files?.[0];
    if (!file) return;

    // Validación del lado del cliente: Máximo 10MB
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg('El archivo es demasiado grande. El máximo permitido es 10MB.');
      setSelectedFile(null);
      return;
    }
    
    setSelectedFile(file);
  };

  const handleSubmit = () => {
    if (selectedFile) {
      submitMutation.mutate(selectedFile);
    }
  };

  if (loadingProject || loadingSubmission) {
    return <Box display="flex" justifyContent="center" mt={10}><CircularProgress /></Box>;
  }

  if (!project) return <Typography color="error">Proyecto no encontrado.</Typography>;

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', mt: 4 }}>
      <Typography variant="h3" gutterBottom>{project.title}</Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Fecha límite: {new Date(project.due_date).toLocaleDateString()}
      </Typography>
      
      <Card sx={{ mt: 3, mb: 4, bgcolor: '#f8f9fa' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Instrucciones</Typography>
          <Typography variant="body1">{project.description}</Typography>
        </CardContent>
      </Card>

      <Typography variant="h5" gutterBottom>Tu Entrega</Typography>
      <Divider sx={{ mb: 3 }} />

      {/* Si ya hay una entrega, mostramos el estado en lugar del formulario */}
      {submission ? (
        <Alert icon={<CheckCircleIcon fontSize="inherit" />} severity="success" sx={{ mb: 3 }}>
          <Typography variant="subtitle1" fontWeight="bold">Proyecto entregado con éxito</Typography>
          <Typography variant="body2">
            Entregado el: {new Date(submission.submitted_at).toLocaleString()}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            Estado: {submission.status === 'reviewed' ? 'Revisado por pares' : 'Pendiente de revisión'}
          </Typography>
          {submission.peer_score && (
            <Typography variant="body1" sx={{ mt: 2, fontWeight: 'bold' }}>
              Calificación: {submission.peer_score}/100
            </Typography>
          )}
          {submission.peer_feedback && (
            <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
              Comentario: "{submission.peer_feedback}"
            </Typography>
          )}
        </Alert>
      ) : (
        /* Formulario de subida */
        <Box>
          {errorMsg && <Alert severity="error" sx={{ mb: 2 }}>{errorMsg}</Alert>}
          
          <Box sx={{ border: '2px dashed #ccc', borderRadius: 2, p: 4, textAlign: 'center', bgcolor: '#fafafa' }}>
            <input
              accept=".pdf,.zip,.docx"
              style={{ display: 'none' }}
              id="raised-button-file"
              type="file"
              onChange={handleFileChange}
              disabled={submitMutation.isPending}
            />
            <label htmlFor="raised-button-file">
              <Button 
                variant="outlined" 
                component="span" 
                startIcon={<CloudUploadIcon />}
                size="large"
                disabled={submitMutation.isPending}
              >
                Seleccionar Archivo
              </Button>
            </label>
            
            {selectedFile && (
              <Typography variant="body1" sx={{ mt: 2, color: 'primary.main', fontWeight: 'bold' }}>
                Archivo seleccionado: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </Typography>
            )}
            
            <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 2 }}>
              Formatos aceptados: PDF, ZIP, DOCX. Tamaño máximo: 10MB.
            </Typography>
          </Box>

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              size="large"
              onClick={handleSubmit}
              disabled={!selectedFile || submitMutation.isPending}
            >
              {submitMutation.isPending ? 'Subiendo...' : 'Entregar Proyecto'}
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
}