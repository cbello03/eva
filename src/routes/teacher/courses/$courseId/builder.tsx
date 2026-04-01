import React from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Box, Typography, CircularProgress, Button, Accordion, AccordionSummary, AccordionDetails, List, ListItem, ListItemText, IconButton, Paper } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import EditIcon from '@mui/icons-material/Edit';
import { useCourse } from '../../../../features/courses/hooks'; // Reutilizamos el hook público del curso

export const Route = createFileRoute('/teacher/courses/$courseId/builder')({
  component: CourseBuilder,
});

function CourseBuilder() {
  const { courseId } = Route.useParams();
  const { data: course, isLoading } = useCourse(courseId);

  if (isLoading) return <Box display="flex" justifyContent="center" mt={10}><CircularProgress /></Box>;
  if (!course) return <Typography color="error">Curso no encontrado.</Typography>;

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4">Constructor de Curso</Typography>
          <Typography variant="subtitle1" color="text.secondary">{course.title}</Typography>
        </Box>
        <Button variant="contained" color="primary" startIcon={<AddCircleOutlineIcon />}>
          Nueva Unidad
        </Button>
      </Box>

      <Paper sx={{ p: 2, bgcolor: '#f5f7fa' }}>
        {course.units?.map((unit) => (
          <Accordion key={unit.id} defaultExpanded sx={{ mb: 1 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center', pr: 2 }}>
                <Typography variant="h6">
                  Unidad {unit.order}: {unit.title}
                </Typography>
                <IconButton size="small" onClick={(e) => e.stopPropagation()}>
                  <EditIcon fontSize="small" />
                </IconButton>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <List disablePadding>
                {unit.lessons.map((lesson) => (
                  <ListItem 
                    key={lesson.id} 
                    sx={{ bgcolor: 'white', mb: 1, borderRadius: 1, border: '1px solid #eee' }}
                    secondaryAction={
                      <Button size="small" variant="text">Editar Ejercicios</Button>
                    }
                  >
                    <ListItemText 
                      primary={`${unit.order}.${lesson.order} ${lesson.title}`} 
                    />
                  </ListItem>
                ))}
                <ListItem sx={{ justifyContent: 'center', mt: 1 }}>
                  <Button size="small" startIcon={<AddCircleOutlineIcon />} color="secondary">
                    Agregar Lección
                  </Button>
                </ListItem>
              </List>
            </AccordionDetails>
          </Accordion>
        ))}
      </Paper>
    </Box>
  );
}