import React, { useState } from 'react';
import { createFileRoute, Link, useParams } from '@tanstack/react-router';
import { Typography, Box, Button, Card, CardContent, Divider, Chip, IconButton } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PlayCircleOutlineIcon from '@mui/icons-material/PlayCircleOutline';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { motion } from 'framer-motion';

import { useCourse } from '../../../../features/courses/hooks';

export const Route = createFileRoute('/courses/$courseId/lessons/$lessonId')({
  component: LessonViewer,
});

function LessonViewer() {
  const { courseId, lessonId } = Route.useParams();
  const { data: course } = useCourse(courseId);
  const [exerciseCompleted, setExerciseCompleted] = useState(false);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);

  // Buscar la lección específica para el encabezado (comparando id convertido a string)
  const currentUnit = course?.units?.find(u => u.lessons.some(l => l.id.toString() === lessonId));
  const currentLesson = currentUnit?.lessons.find(l => l.id.toString() === lessonId);

  const quizOptions = [
    "Escalabilidad independiente", 
    "Menor base de código unificada", 
    "Despliegue rápido", 
    "Dependencia fuerte compartida"
  ];
  const correctIndex = 3;

  const handleCheckAnswer = () => {
    if (selectedOption === correctIndex) {
      setExerciseCompleted(true);
    } else {
      alert("Respuesta incorrecta. ¡Inténtalo de nuevo!");
    }
  };

  return (
    <Box sx={{ maxWidth: 900, mx: 'auto', pb: 8 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton component={Link} to={`/courses/${courseId}`} sx={{ color: 'white', mr: 2, bgcolor: '#1e293b' }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          {currentLesson ? `${currentUnit?.order}.${currentLesson.order} ${currentLesson.title}` : 'Visor de Lección'}
        </Typography>
        <Chip label="Unidad Actual" size="small" sx={{ ml: 3, bgcolor: 'rgba(99,102,241,0.2)', color: '#818cf8', fontWeight: 600 }} />
      </Box>

      {/* Rproductor de Video Inmersivo (Simulado) */}
      <Card sx={{ bgcolor: 'black', borderRadius: 4, overflow: 'hidden', mb: 4, position: 'relative', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.4)' }}>
        <Box sx={{ width: '100%', paddingTop: '56.25%', position: 'relative', background: 'radial-gradient(circle, #1e293b 0%, black 100%)' }}>
          <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
            <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
              <IconButton sx={{ color: '#ec4899', width: 90, height: 90 }}>
                <PlayCircleOutlineIcon sx={{ fontSize: 90 }} />
              </IconButton>
            </motion.div>
            <Typography variant="body1" sx={{ mt: 2, color: 'rgba(255,255,255,0.7)' }}>Presiona Play para comenzar el video inmersivo</Typography>
          </Box>
        </Box>
      </Card>

      {/* Contenido Teórico / Markdown Mock */}
      <Card sx={{ bgcolor: '#1e293b', borderRadius: 4, mb: 4 }}>
        <CardContent sx={{ p: { xs: 3, md: 5 } }}>
          <Typography variant="h4" sx={{ mb: 3, fontWeight: 800 }}>Introducción y Conceptos Clave</Typography>
          <Typography variant="body1" sx={{ color: '#cbd5e1', lineHeight: 1.8, mb: 3, fontSize: '1.1rem' }}>
            En esta lección cubriremos los fundamentos de la estructura de datos moderna y cómo impacta en las decisiones de diseño. Las arquitecturas monolíticas están cediendo el paso a los microservicios, lo que genera nuevas necesidades de comunicación entre capas frontales desacopladas.
          </Typography>
          <Box sx={{ bgcolor: '#0f172a', p: 3, borderRadius: 2, borderLeft: '4px solid #6366f1', mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#a78bfa' }}>
              // Ejemplo en pseudocódigo<br/>
              function inicializarSistema() {"{"}<br/>
              &nbsp;&nbsp;console.log("¡Carga completa!");<br/>
              {"}"}
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ color: '#cbd5e1', lineHeight: 1.8, fontSize: '1.1rem' }}>
            Asegúrate de recordar estos conceptos, ya que serán evaluados en el mini-quiz interactivo a continuación. Completar el test sumará XP a tu perfil y validará tu racha de hoy.
          </Typography>
        </CardContent>
      </Card>

      {/* Sección Activa (Evaluación / Gamificación) */}
      <Divider sx={{ my: 6, borderColor: 'rgba(255,255,255,0.1)' }} />
      <Box sx={{ mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckCircleIcon color="success" /> Comprueba tus conocimientos
        </Typography>
        <Typography variant="body2" sx={{ color: '#94a3b8' }}>Gana +50 XP completando este ejercicio interactivo</Typography>
      </Box>
      
      <Card sx={{ bgcolor: '#1e293b', borderRadius: 4, border: exerciseCompleted ? '1px solid #22c55e' : '1px solid rgba(255,255,255,0.1)' }}>
        <CardContent sx={{ p: 4 }}>
          
          <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>¿Cuál de los siguientes no es un beneficio directo de los microservicios?</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 4 }}>
            {quizOptions.map((opt, idx) => (
              <Button 
                key={idx} 
                variant="outlined" 
                onClick={() => setSelectedOption(idx)}
                sx={{ 
                  justifyContent: 'flex-start', py: 2, px: 3, borderRadius: 3, 
                  borderColor: selectedOption === idx ? '#6366f1' : 'rgba(255,255,255,0.1)',
                  bgcolor: selectedOption === idx ? 'rgba(99,102,241,0.1)' : 'transparent',
                  color: selectedOption === idx ? 'white' : '#cbd5e1',
                  textAlign: 'left'
                }}
              >
                {opt}
              </Button>
            ))}
          </Box>
          
          <Button 
            variant="contained" 
            fullWidth 
            disabled={selectedOption === null || exerciseCompleted}
            onClick={handleCheckAnswer}
            sx={{ py: 1.5, borderRadius: 8, fontWeight: 700, bgcolor: exerciseCompleted ? '#22c55e' : 'primary.main' }}
          >
            {exerciseCompleted ? '¡Correcto!' : 'Comprobar'}
          </Button>

          {exerciseCompleted && (
             <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
               <Box sx={{ mt: 4, p: 3, bgcolor: 'rgba(34,197,94,0.1)', borderRadius: 2, textAlign: 'center', border: '1px solid rgba(34,197,94,0.3)' }}>
                 <Typography variant="h6" sx={{ color: '#4ade80', fontWeight: 700, mb: 1 }}>¡Excelente Trabajo!</Typography>
                 <Typography variant="body2" sx={{ color: '#cbd5e1', mb: 3 }}>Has asimilado el conocimiento de esta lección con éxito. Ganaste +50 XP.</Typography>
                 <Button variant="contained" color="primary" component={Link} to={`/courses/${courseId}`} sx={{ fontWeight: 700, borderRadius: 8, background: 'linear-gradient(90deg, #6366f1, #ec4899)' }}>
                   Volver e Ir al Siguiente
                 </Button>
               </Box>
             </motion.div>
          )}
        </CardContent>
      </Card>

    </Box>
  );
}