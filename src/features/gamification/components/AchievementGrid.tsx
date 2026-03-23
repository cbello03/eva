import React from 'react';
import { Grid, Card, CardContent, Typography, Box, Avatar } from '@mui/material';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import LockIcon from '@mui/icons-material/Lock';
import { Achievement } from '../api';

interface Props {
  achievements: Achievement[];
}

export function AchievementGrid({ achievements }: Props) {
  if (!achievements?.length) {
    return <Typography color="text.secondary">Aún no hay logros disponibles en la plataforma.</Typography>;
  }

  return (
    <Grid container spacing={2}>
      {achievements.map((achievement) => (
        <Grid item xs={12} sm={6} md={4} key={achievement.id}>
          {/* Bajamos la opacidad si el logro está bloqueado */}
          <Card sx={{ opacity: achievement.is_unlocked ? 1 : 0.6, height: '100%' }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ 
                bgcolor: achievement.is_unlocked ? 'gold' : 'grey.300',
                color: achievement.is_unlocked ? 'black' : 'grey.600'
              }}>
                {achievement.is_unlocked ? <EmojiEventsIcon /> : <LockIcon />}
              </Avatar>
              <Box>
                <Typography variant="h6">{achievement.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {achievement.description}
                </Typography>
                {achievement.unlocked_at && (
                  <Typography variant="caption" color="primary" display="block" sx={{ mt: 0.5 }}>
                    Obtenido: {new Date(achievement.unlocked_at).toLocaleDateString()}
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}