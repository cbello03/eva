"use client";

import { use } from "react";
import { Container, Typography, Button, Box } from "@mui/material";
import { ArrowBack as ArrowBackIcon } from "@mui/icons-material";
import Link from "next/link";
import ChatRoom from "@/features/social/components/ChatRoom";

interface ChatPageProps {
  params: Promise<{ courseId: string }>;
}

export default function ChatPage({ params }: ChatPageProps) {
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
        Back to Course
      </Button>

      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1">
          Course Chat
        </Typography>
      </Box>

      <ChatRoom courseId={courseId} />
    </Container>
  );
}
