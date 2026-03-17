import { Container, Typography, Card, CardContent, CardMedia, Button, Box, LinearProgress } from '@mui/material';
// Importamos Grid2 que es la versión moderna para evitar errores de TypeScript
import Grid from '@mui/material/Grid';

const COURSES = [
  { id: 1, title: 'Matemáticas Avanzadas', teacher: 'Dr. Pérez', progress: 75, image: 'https://picsum.photos/200/120?random=1' },
  { id: 2, title: 'Historia Universal', teacher: 'Lic. García', progress: 30, image: 'https://picsum.photos/200/120?random=2' },
  { id: 3, title: 'Programación Web', teacher: 'Ing. López', progress: 10, image: 'https://picsum.photos/200/120?random=3' },
];

export const StudentDashboard = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom color="primary">
          ¡Hola, Estudiante! 👋
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Aquí tienes un resumen de tus cursos y progreso actual.
        </Typography>
      </Box>

      {/* Usamos el nuevo sistema de Grid que no necesita la palabra "item" */}
      <Grid container spacing={3}>
        {COURSES.map((course) => (
          <Grid key={course.id} size={{ xs: 12, sm: 6, md: 4 }}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 3, boxShadow: 3 }}>
              <CardMedia component="img" height="140" image={course.image} alt={course.title} />
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography gutterBottom variant="h6" fontWeight="bold">
                  {course.title}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Profesor: {course.teacher}
                </Typography>
                <Box sx={{ width: '100%', mr: 1 }}>
                    <Typography variant="caption" color="textSecondary">Progreso: {course.progress}%</Typography>
                    <LinearProgress variant="determinate" value={course.progress} sx={{ height: 8, borderRadius: 5, mt: 1 }} />
                </Box>
              </CardContent>
              <Box sx={{ p: 2 }}>
                <Button fullWidth variant="contained" sx={{ backgroundColor: '#2e7d32' }}>
                  Continuar Lectura
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};