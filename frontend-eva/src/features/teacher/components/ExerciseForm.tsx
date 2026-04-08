"use client";

import { useState } from "react";
import {
  Box,
  TextField,
  MenuItem,
  Button,
  Typography,
  IconButton,
  Paper,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";

type ExerciseType = "multiple_choice" | "fill_blank" | "matching" | "free_text";

interface ExerciseFormData {
  question_text: string;
  exercise_type: ExerciseType;
  config: Record<string, unknown>;
  difficulty: number;
  topic: string;
}

interface ExerciseFormProps {
  onSubmit: (data: ExerciseFormData) => void;
  isSubmitting?: boolean;
}

export default function ExerciseForm({ onSubmit, isSubmitting }: ExerciseFormProps) {
  const [exerciseType, setExerciseType] = useState<ExerciseType>("multiple_choice");
  const [questionText, setQuestionText] = useState("");
  const [difficulty, setDifficulty] = useState(1);
  const [topic, setTopic] = useState("");

  // Multiple choice state
  const [mcOptions, setMcOptions] = useState(["", ""]);
  const [mcCorrectIndex, setMcCorrectIndex] = useState(0);

  // Fill blank state
  const [blankPosition, setBlankPosition] = useState(0);
  const [acceptedAnswers, setAcceptedAnswers] = useState([""]);

  // Matching state
  const [matchingPairs, setMatchingPairs] = useState([
    { left: "", right: "" },
    { left: "", right: "" },
  ]);

  // Free text state
  const [modelAnswer, setModelAnswer] = useState("");
  const [rubric, setRubric] = useState("");

  const handleSubmit = () => {
    let config: Record<string, unknown> = {};

    switch (exerciseType) {
      case "multiple_choice":
        config = { options: mcOptions, correct_index: mcCorrectIndex };
        break;
      case "fill_blank":
        config = {
          blank_position: blankPosition,
          accepted_answers: acceptedAnswers.filter(Boolean),
        };
        break;
      case "matching":
        config = { pairs: matchingPairs };
        break;
      case "free_text":
        config = { model_answer: modelAnswer, rubric };
        break;
    }

    onSubmit({
      question_text: questionText,
      exercise_type: exerciseType,
      config,
      difficulty,
      topic,
    });
  };

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle1" gutterBottom>
        New Exercise
      </Typography>

      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <TextField
          label="Question"
          value={questionText}
          onChange={(e) => setQuestionText(e.target.value)}
          multiline
          rows={2}
          required
        />

        <Box sx={{ display: "flex", gap: 2 }}>
          <TextField
            select
            label="Type"
            value={exerciseType}
            onChange={(e) => setExerciseType(e.target.value as ExerciseType)}
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="multiple_choice">Multiple Choice</MenuItem>
            <MenuItem value="fill_blank">Fill in the Blank</MenuItem>
            <MenuItem value="matching">Matching</MenuItem>
            <MenuItem value="free_text">Free Text</MenuItem>
          </TextField>

          <TextField
            select
            label="Difficulty"
            value={difficulty}
            onChange={(e) => setDifficulty(Number(e.target.value))}
            sx={{ minWidth: 100 }}
          >
            {[1, 2, 3, 4, 5].map((d) => (
              <MenuItem key={d} value={d}>{d}</MenuItem>
            ))}
          </TextField>

          <TextField
            label="Topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            sx={{ flex: 1 }}
          />
        </Box>

        {/* Type-specific config */}
        {exerciseType === "multiple_choice" && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Options (select the correct one)
            </Typography>
            {mcOptions.map((opt, i) => (
              <Box key={i} sx={{ display: "flex", gap: 1, mt: 1, alignItems: "center" }}>
                <input
                  type="radio"
                  name="correct"
                  checked={mcCorrectIndex === i}
                  onChange={() => setMcCorrectIndex(i)}
                  aria-label={`Mark option ${i + 1} as correct`}
                />
                <TextField
                  size="small"
                  value={opt}
                  onChange={(e) => {
                    const next = [...mcOptions];
                    next[i] = e.target.value;
                    setMcOptions(next);
                  }}
                  placeholder={`Option ${i + 1}`}
                  sx={{ flex: 1 }}
                />
                {mcOptions.length > 2 && (
                  <IconButton
                    size="small"
                    onClick={() => {
                      setMcOptions(mcOptions.filter((_, j) => j !== i));
                      if (mcCorrectIndex >= mcOptions.length - 1)
                        setMcCorrectIndex(0);
                    }}
                    aria-label="Remove option"
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                )}
              </Box>
            ))}
            <Button
              size="small"
              startIcon={<AddIcon />}
              onClick={() => setMcOptions([...mcOptions, ""])}
              sx={{ mt: 1 }}
            >
              Add Option
            </Button>
          </Box>
        )}

        {exerciseType === "fill_blank" && (
          <Box>
            <TextField
              label="Blank Position (word index)"
              type="number"
              size="small"
              value={blankPosition}
              onChange={(e) => setBlankPosition(Number(e.target.value))}
              sx={{ mb: 1 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
              Accepted Answers
            </Typography>
            {acceptedAnswers.map((ans, i) => (
              <Box key={i} sx={{ display: "flex", gap: 1, mb: 0.5 }}>
                <TextField
                  size="small"
                  value={ans}
                  onChange={(e) => {
                    const next = [...acceptedAnswers];
                    next[i] = e.target.value;
                    setAcceptedAnswers(next);
                  }}
                  placeholder={`Answer ${i + 1}`}
                  sx={{ flex: 1 }}
                />
                {acceptedAnswers.length > 1 && (
                  <IconButton
                    size="small"
                    onClick={() => setAcceptedAnswers(acceptedAnswers.filter((_, j) => j !== i))}
                    aria-label="Remove answer"
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                )}
              </Box>
            ))}
            <Button
              size="small"
              startIcon={<AddIcon />}
              onClick={() => setAcceptedAnswers([...acceptedAnswers, ""])}
            >
              Add Answer
            </Button>
          </Box>
        )}

        {exerciseType === "matching" && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Matching Pairs
            </Typography>
            {matchingPairs.map((pair, i) => (
              <Box key={i} sx={{ display: "flex", gap: 1, mt: 1, alignItems: "center" }}>
                <TextField
                  size="small"
                  value={pair.left}
                  onChange={(e) => {
                    const next = [...matchingPairs];
                    next[i] = { ...next[i], left: e.target.value };
                    setMatchingPairs(next);
                  }}
                  placeholder="Left"
                  sx={{ flex: 1 }}
                />
                <Typography variant="body2">→</Typography>
                <TextField
                  size="small"
                  value={pair.right}
                  onChange={(e) => {
                    const next = [...matchingPairs];
                    next[i] = { ...next[i], right: e.target.value };
                    setMatchingPairs(next);
                  }}
                  placeholder="Right"
                  sx={{ flex: 1 }}
                />
                {matchingPairs.length > 2 && (
                  <IconButton
                    size="small"
                    onClick={() => setMatchingPairs(matchingPairs.filter((_, j) => j !== i))}
                    aria-label="Remove pair"
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                )}
              </Box>
            ))}
            <Button
              size="small"
              startIcon={<AddIcon />}
              onClick={() => setMatchingPairs([...matchingPairs, { left: "", right: "" }])}
              sx={{ mt: 1 }}
            >
              Add Pair
            </Button>
          </Box>
        )}

        {exerciseType === "free_text" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            <TextField
              label="Model Answer"
              value={modelAnswer}
              onChange={(e) => setModelAnswer(e.target.value)}
              multiline
              rows={2}
            />
            <TextField
              label="Rubric"
              value={rubric}
              onChange={(e) => setRubric(e.target.value)}
              multiline
              rows={2}
            />
          </Box>
        )}

        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!questionText.trim() || isSubmitting}
        >
          {isSubmitting ? "Adding…" : "Add Exercise"}
        </Button>
      </Box>
    </Paper>
  );
}
