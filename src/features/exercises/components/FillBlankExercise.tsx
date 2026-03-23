import React, { useState } from 'react';
import { Box, Typography, TextField, Button } from '@mui/material';
import { Exercise } from '../types';

interface Props {
  exercise: Exercise;
  onSubmit: (answer: any) => void;
  isSubmitting: boolean;
}

export function FillBlankExercise({ exercise, onSubmit, isSubmitting }: Props) {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim()) return;
    
    // El backend evaluará esta cadena contra la lista de 'accepted_answers' de forma insensible a mayúsculas
    onSubmit({ submitted_text: inputValue.trim() });
    setInputValue('');
  };

  // Asumimos que el backend envía la pregunta con un marcador, por ejemplo: "El OSI capa 3 es la capa de ____."
  // O podemos usar el blank_position si viene como un arreglo de palabras.
  // Para este ejemplo, usaremos un texto simple donde el usuario completa la idea.
  
  return (
    <Box sx={{ mt: 4, width: '100%', maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom>
        Completa el espacio en blanco:
      </Typography>
      
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="h6" component="span">
          {exercise.question_text.split('____')[0]}
        </Typography>
        
        <TextField
          variant="standard"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="escribe aquí"
          disabled={isSubmitting}
          autoFocus
          inputProps={{ style: { fontSize: '1.25rem', textAlign: 'center' } }}
        />
        
        <Typography variant="h6" component="span">
          {exercise.question_text.split('____')[1]}
        </Typography>
      </Box>

      <Box sx={{ mt: 5, display: 'flex', justifyContent: 'flex-end' }}>
        <Button 
          variant="contained" 
          color="primary" 
          size="large"
          onClick={handleSubmit} 
          disabled={!inputValue.trim() || isSubmitting}
        >
          {isSubmitting ? 'Comprobando...' : 'Comprobar Respuesta'}
        </Button>
      </Box>
    </Box>
  );
}