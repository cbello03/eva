import React, { useState } from 'react';
import { Radio, RadioGroup, FormControlLabel, FormControl, Button, Box, Typography } from '@mui/material';
import { Exercise } from '../types';

interface Props {
  exercise: Exercise;
  onSubmit: (answer: any) => void;
  isSubmitting: boolean;
}

export function MultipleChoiceExercise({ exercise, onSubmit, isSubmitting }: Props) {
  const [selectedValue, setSelectedValue] = useState<string>('');

  const handleSubmit = () => {
    // El backend espera el índice de la opción seleccionada
    onSubmit({ selected_index: parseInt(selectedValue, 10) });
    setSelectedValue(''); // Limpiar selección para el siguiente ejercicio
  };

  // Asumimos que config tiene la forma: { options: ["Opción A", "Opción B", ...] }
  const options: string[] = exercise.config?.options || [];

  return (
    <Box sx={{ mt: 4, width: '100%', maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom>
        {exercise.question_text}
      </Typography>
      
      <FormControl component="fieldset" sx={{ mt: 2, width: '100%' }}>
        <RadioGroup 
          value={selectedValue} 
          onChange={(e) => setSelectedValue(e.target.value)}
        >
          {options.map((option, idx) => (
            <FormControlLabel 
              key={idx} 
              value={idx.toString()} 
              control={<Radio />} 
              label={option} 
              sx={{ 
                border: '1px solid #e0e0e0', 
                borderRadius: 2, 
                mb: 1, 
                p: 1,
                '&:hover': { backgroundColor: '#f5f5f5' }
              }}
            />
          ))}
        </RadioGroup>
      </FormControl>

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
        <Button 
          variant="contained" 
          color="primary" 
          size="large"
          onClick={handleSubmit} 
          disabled={selectedValue === '' || isSubmitting}
        >
          {isSubmitting ? 'Comprobando...' : 'Comprobar Respuesta'}
        </Button>
      </Box>
    </Box>
  );
}