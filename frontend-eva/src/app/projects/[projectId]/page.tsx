"use client";

import { use, useState } from "react";
import {
  Container,
  Button,
  Box,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
} from "@mui/material";
import { ArrowBack as ArrowBackIcon } from "@mui/icons-material";
import Link from "next/link";
import { useProject, useSubmitProject, useReviews, useSubmitReview } from "@/features/projects/hooks";
import ProjectDetail from "@/features/projects/components/ProjectDetail";
import SubmissionForm from "@/features/projects/components/SubmissionForm";
import ReviewList from "@/features/projects/components/ReviewList";
import ReviewForm from "@/features/projects/components/ReviewForm";

interface ProjectPageProps {
  params: Promise<{ projectId: string }>;
}

export default function ProjectPage({ params }: ProjectPageProps) {
  const { projectId: projectIdStr } = use(params);
  const projectId = Number(projectIdStr);
  const [tab, setTab] = useState(0);
  const [submissionId, setSubmissionId] = useState<number | null>(null);

  const { data: project, isLoading, error } = useProject(projectId);
  const submitMutation = useSubmitProject(projectId);
  const { data: reviews } = useReviews(submissionId ?? 0);
  const reviewMutation = useSubmitReview(submissionId ?? 0);

  if (isLoading) {
    return (
      <Container maxWidth="md" sx={{ py: 4, textAlign: "center" }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !project) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">Error al cargar el proyecto.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Button
        component={Link}
        href="/projects"
        startIcon={<ArrowBackIcon />}
        sx={{ mb: 2 }}
      >
        Volver a Proyectos
      </Button>

      <ProjectDetail project={project} />

      <Box sx={{ mt: 3 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Enviar" />
          <Tab label="Reseñas" disabled={!submissionId} />
          <Tab label="Evaluar" disabled={!submissionId} />
        </Tabs>

        <Box sx={{ mt: 2 }}>
          {tab === 0 && (
            <>
              {submitMutation.isSuccess && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  ¡Proyecto enviado exitosamente!
                </Alert>
              )}
              {submitMutation.isError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  Error en el envío. Por favor, inténtalo de nuevo.
                </Alert>
              )}
              <SubmissionForm
                onSubmit={(data) => {
                  submitMutation.mutate(data, {
                    onSuccess: (submission) => setSubmissionId(submission.id),
                  });
                }}
                isPending={submitMutation.isPending}
              />
            </>
          )}

          {tab === 1 && submissionId && (
            <ReviewList
              reviews={reviews ?? []}
              rubric={project.rubric}
            />
          )}

          {tab === 2 && submissionId && (
            <>
              {reviewMutation.isSuccess && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  ¡Evaluación enviada!
                </Alert>
              )}
              <ReviewForm
                rubric={project.rubric}
                onSubmit={(data) => reviewMutation.mutate(data)}
                isPending={reviewMutation.isPending}
              />
            </>
          )}
        </Box>
      </Box>
    </Container>
  );
}
