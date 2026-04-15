"use client";

import { useState, useRef } from "react";
import {
  Box,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Alert,
} from "@mui/material";
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";

interface SubmissionFormProps {
  onSubmit: (data: { description: string; files: File[] }) => void;
  isPending?: boolean;
}

const MAX_FILES = 5;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function SubmissionForm({ onSubmit, isPending }: SubmissionFormProps) {
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? []);
    setError(null);

    for (const file of selected) {
      if (file.size > MAX_FILE_SIZE) {
        setError(`El archivo "${file.name}" excede el límite de 10MB.`);
        return;
      }
    }

    const combined = [...files, ...selected];
    if (combined.length > MAX_FILES) {
      setError(`Máximo ${MAX_FILES} archivos permitidos.`);
      return;
    }

    setFiles(combined);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;
    onSubmit({ description: description.trim(), files });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <TextField
        label="Descripción del envío"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        required
        multiline
        rows={4}
        fullWidth
      />

      <Box>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          hidden
          onChange={handleFileChange}
        />
        <Button
          variant="outlined"
          startIcon={<UploadIcon />}
          onClick={() => fileInputRef.current?.click()}
          disabled={files.length >= MAX_FILES}
        >
          Adjuntar archivos ({files.length}/{MAX_FILES})
        </Button>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      {files.length > 0 && (
        <List dense>
          {files.map((file, i) => (
            <ListItem
              key={`${file.name}-${i}`}
              secondaryAction={
                <IconButton edge="end" onClick={() => removeFile(i)}>
                  <DeleteIcon fontSize="small" />
                </IconButton>
              }
            >
              <ListItemText
                primary={file.name}
                secondary={`${(file.size / 1024).toFixed(1)} KB`}
              />
            </ListItem>
          ))}
        </List>
      )}

      <Button
        type="submit"
        variant="contained"
        disabled={isPending || !description.trim()}
        sx={{ alignSelf: "flex-end" }}
      >
        {isPending ? "Enviando…" : "Enviar proyecto"}
      </Button>
    </Box>
  );
}
