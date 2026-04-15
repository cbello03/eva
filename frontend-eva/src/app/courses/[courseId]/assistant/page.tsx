"use client";

import { use } from "react";
import { Container, Typography, Button, Box } from "@mui/material";
import { ArrowBack as ArrowBackIcon } from "@mui/icons-material";
import Link from "next/link";
import CourseAssistant from "@/features/social/components/CourseAssistant";

interface AssistantPageProps {
  params: Promise<{ courseId: string }>;
}

export default function AssistantPage({ params }: AssistantPageProps) {
  const { courseId: courseIdStr } = use(params);
  const courseId = Number(courseIdStr);

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Button
        component={Link}
        href={`/courses/${courseId}`}
        startIcon={<ArrowBackIcon />}
        sx={{ mb: 2 }}
      >
        Volver al curso
      </Button>

      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1">
          Asistente IA del curso
        </Typography>
      </Box>

      <CourseAssistant courseId={courseId} />
    </Container>
  );
}
