"use client";

import { useState } from "react";
import { useEffect } from "react";
import Link from "next/link";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  TextField,
  Typography,
  Link as MuiLink,
} from "@mui/material";
import { useCourseChatbot } from "@/features/social/hooks";
import type { ChatbotTurn } from "@/features/social/api";

interface CourseAssistantProps {
  courseId: number;
}

export default function CourseAssistant({ courseId }: CourseAssistantProps) {
  const askMutation = useCourseChatbot(courseId);
  const storageKey = `eva-course-assistant-history-${courseId}`;
  const [question, setQuestion] = useState("");
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const [mode, setMode] = useState<"brief" | "detailed">("brief");
  const [history, setHistory] = useState<ChatbotTurn[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (!raw) return [];
      const parsed = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) return [];
      return parsed
        .filter(
          (item): item is ChatbotTurn =>
            typeof item === "object" &&
            item !== null &&
            "role" in item &&
            "content" in item &&
            ((item as { role: string }).role === "user" ||
              (item as { role: string }).role === "assistant") &&
            typeof (item as { content: string }).content === "string",
        )
        .slice(-8);
    } catch {
      return [];
    }
  });
  const [confirmClearOpen, setConfirmClearOpen] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(history.slice(-8)));
    } catch {
      // Best-effort persistence only.
    }
  }, [history, storageKey]);

  const handleAsk = () => {
    const trimmed = question.trim();
    if (!trimmed) return;
    setLastQuestion(trimmed);
    askMutation.mutate(
      {
        question: trimmed,
        mode,
        history: history.slice(-8),
      },
      {
        onSuccess: (data) => {
          setHistory((prev) => [
            ...prev.slice(-7),
            { role: "user", content: trimmed },
            { role: "assistant", content: data.answer },
          ]);
        },
      },
    );
  };

  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Asistente del curso
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Puedes hacer preguntas sobre el contenido de este curso. El asistente no responde temas fuera de este curso.
      </Typography>
      <Box sx={{ mb: 2 }}>
        <Button
          variant="text"
          size="small"
          color="inherit"
          onClick={() => setConfirmClearOpen(true)}
          disabled={history.length === 0}
        >
          Limpiar historial
        </Button>
      </Box>

      <Box sx={{ display: "flex", gap: 1, mb: 2, alignItems: "center", flexWrap: "wrap" }}>
        <FormControl size="small" sx={{ minWidth: 170 }}>
          <InputLabel id="assistant-mode-label">Modo</InputLabel>
          <Select
            labelId="assistant-mode-label"
            value={mode}
            label="Modo"
            onChange={(e) => setMode(e.target.value as "brief" | "detailed")}
            disabled={askMutation.isPending}
          >
            <MenuItem value="brief">Respuesta breve</MenuItem>
            <MenuItem value="detailed">Explicacion detallada</MenuItem>
          </Select>
        </FormControl>
        <TextField
          fullWidth
          size="small"
          placeholder="Ejemplo: ¿Que vimos en la unidad 1?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleAsk();
          }}
          disabled={askMutation.isPending}
        />
        <Button
          variant="contained"
          onClick={handleAsk}
          disabled={askMutation.isPending || !question.trim()}
        >
          Preguntar
        </Button>
      </Box>

      {askMutation.isPending && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, py: 1 }}>
          <CircularProgress size={20} />
          <Typography variant="body2" color="text.secondary">
            Pensando respuesta...
          </Typography>
        </Box>
      )}

      {askMutation.isError && (
        <Alert severity="error" sx={{ mt: 1 }}>
          No se pudo obtener respuesta del asistente. Verifica la configuración de Gemini e inténtalo de nuevo.
        </Alert>
      )}

      {askMutation.data && (
        <Box sx={{ mt: 2 }}>
          {lastQuestion && (
            <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
              Tu pregunta
            </Typography>
          )}
          {lastQuestion && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              {lastQuestion}
            </Typography>
          )}

          <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
            Respuesta del asistente
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
            Modo: {askMutation.data.mode === "brief" ? "breve" : "detallada"}
          </Typography>
          <Typography variant="body2">{askMutation.data.answer}</Typography>
          {askMutation.data.sources.length > 0 && (
            <Box sx={{ mt: 1.25 }}>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.25 }}>
                Fuentes del curso
              </Typography>
              {askMutation.data.sources.map((source, idx) => (
                <MuiLink
                  key={`source-${idx}`}
                  component={Link}
                  href={source.href}
                  underline="hover"
                  color="text.secondary"
                  sx={{ display: "block", fontSize: "0.75rem" }}
                >
                  - {source.label}
                </MuiLink>
              ))}
            </Box>
          )}
        </Box>
      )}

      {history.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Historial reciente
          </Typography>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.75, maxHeight: 220, overflowY: "auto" }}>
            {history.slice(-8).map((turn, idx) => (
              <Typography key={`${turn.role}-${idx}`} variant="caption" color="text.secondary">
                <strong>{turn.role === "user" ? "Tú" : "Asistente"}:</strong> {turn.content}
              </Typography>
            ))}
          </Box>
        </Box>
      )}

      <Dialog open={confirmClearOpen} onClose={() => setConfirmClearOpen(false)}>
        <DialogTitle>Limpiar historial</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            ¿Seguro que quieres borrar el historial reciente de este asistente?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmClearOpen(false)}>Cancelar</Button>
          <Button
            color="error"
            onClick={() => {
              setHistory([]);
              if (typeof window !== "undefined") {
                try {
                  window.localStorage.removeItem(storageKey);
                } catch {
                  // Best-effort only.
                }
              }
              setConfirmClearOpen(false);
            }}
          >
            Limpiar
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}
