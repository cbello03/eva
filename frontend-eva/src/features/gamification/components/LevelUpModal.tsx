"use client";

import {
  Dialog,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
} from "@mui/material";
import StarIcon from "@mui/icons-material/Star";

interface LevelUpModalProps {
  open: boolean;
  newLevel: number;
  onClose: () => void;
}

export default function LevelUpModal({
  open,
  newLevel,
  onClose,
}: LevelUpModalProps) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogContent sx={{ textAlign: "center", py: 4 }}>
        <Box
          sx={{
            width: 80,
            height: 80,
            borderRadius: "50%",
            bgcolor: "primary.main",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            mx: "auto",
            mb: 2,
          }}
        >
          <StarIcon sx={{ fontSize: 48, color: "primary.contrastText" }} />
        </Box>
        <Typography variant="h5" gutterBottom>
          ¡Subiste de nivel!
        </Typography>
        <Typography variant="h3" color="primary" sx={{ fontWeight: 700 }}>
          {newLevel}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          ¡Felicidades! Sigue aprendiendo para alcanzar el siguiente nivel.
        </Typography>
      </DialogContent>
      <DialogActions sx={{ justifyContent: "center", pb: 3 }}>
        <Button variant="contained" onClick={onClose}>
          Continuar
        </Button>
      </DialogActions>
    </Dialog>
  );
}
