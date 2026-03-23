import React from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { Typography, Grid, Card, CardContent, CardActions, Button, CircularProgress, Box } from '@mui/material';
import { useCourses } from '../../features/courses/hooks';

export const Route = createFileRoute('/courses/')({
  component: CourseList,
});

function CourseList() {
  const { data: courses, isLoading, error } = useCourses();

  if (isLoading) return <Box display="flex" justifyContent="center"><CircularProgress /></Box>;
  if (error) return <Typography color="error">Error al cargar los cursos.</Typography>;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Catálogo de Cursos</Typography>
      <Grid container spacing={3}>
        {courses?.map((course) => (
          <Grid item xs={12} sm={6} md={4} key={course.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{course.title}</Typography>
                <Typography variant="body2" color="textSecondary" noWrap>
                  {course.description}
                </Typography>
              </CardContent>
              <CardActions>
                <Button size="small" component={Link} to={`/courses/${course.id}`}>
                  Ver Detalles
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}