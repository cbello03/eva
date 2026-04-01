import React from 'react';
import { createFileRoute, Link, useParams } from '@tanstack/react-router';
import { Typography, Box, Button, CircularProgress, Accordion, AccordionSummary, AccordionDetails, List, ListItem, ListItemButton, ListItemText } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useCourse, useEnroll } from '../../features/courses/hooks';

export const Route = createFileRoute('/courses/$courseId')({
  component: CourseDetail,
});

function CourseDetail() {
  const { courseId } = Route.useParams();
  const { data: course, isLoading } = useCourse(courseId);
  const enrollMutation = useEnroll();

  if (isLoading) return <Box display="flex" justifyContent="center"><CircularProgress /></Box>;
  if (!course) return <Typography>Curso no encontrado.</Typography>;

  const handleEnroll = () => {
    enrollMutation.mutate(courseId);
  };

  return (
    <Box>
      <Typography variant="h3" gutterBottom>{course.title}</Typography>
      <Typography variant="body1" paragraph>{course.description}</Typography>
      
      <Button 
        variant="contained" 
        color="primary" 
        onClick={handleEnroll}
        disabled={enrollMutation.isPending}
        sx={{ mb: 4 }}
      >
        {enrollMutation.isPending ? 'Inscribiendo...' : 'Inscribirse al Curso'}
      </Button>

      <Typography variant="h5" gutterBottom>Contenido del Curso</Typography>
      
      {course.units?.map((unit) => (
        <Accordion key={unit.id}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">Unidad {unit.order}: {unit.title}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List>
              {unit.lessons.map((lesson) => (
                <ListItemButton 
                  key={lesson.id} 
                  component={Link} 
                  to={`/courses/${course.id}/lessons/${lesson.id}`}
                  sx={{ borderRadius: 2, mb: 1, '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' } }}
                >
                  <ListItemText primary={`${unit.order}.${lesson.order} ${lesson.title}`} />
                </ListItemButton>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}