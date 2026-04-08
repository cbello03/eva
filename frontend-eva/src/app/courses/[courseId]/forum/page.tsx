"use client";

import { use, useMemo, useState } from "react";
import {
  Container,
  Typography,
  Button,
  Box,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
} from "@mui/material";
import { Add as AddIcon, ArrowBack as ArrowBackIcon } from "@mui/icons-material";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  useForumThreads,
  useThread,
  useCreateThread,
  useCreateReply,
  useUpvote,
} from "@/features/social/hooks";
import { flagPost } from "@/features/social/api";
import ThreadList from "@/features/social/components/ThreadList";
import ThreadDetail from "@/features/social/components/ThreadDetail";
import ThreadForm from "@/features/social/components/ThreadForm";
import ReplyForm from "@/features/social/components/ReplyForm";

interface ForumPageProps {
  params: Promise<{ courseId: string }>;
}

export default function ForumPage({ params }: ForumPageProps) {
  const { courseId: courseIdStr } = use(params);
  const courseId = Number(courseIdStr);
  const searchParams = useSearchParams();
  const threadIdParam = searchParams.get("thread");
  const selectedThreadId = threadIdParam ? Number(threadIdParam) : null;

  const [showNewThread, setShowNewThread] = useState(false);

  const {
    data: threadsData,
    isLoading: threadsLoading,
    error: threadsError,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
  } = useForumThreads(courseId);

  const {
    data: threadDetail,
    isLoading: threadLoading,
  } = useThread(selectedThreadId ?? 0);

  const createThreadMutation = useCreateThread(courseId);
  const createReplyMutation = useCreateReply(selectedThreadId ?? 0);
  const upvoteMutation = useUpvote(selectedThreadId ?? 0);

  const allThreads = useMemo(
    () => threadsData?.pages.flatMap((p) => p.results) ?? [],
    [threadsData],
  );

  const handleCreateThread = (data: { title: string; body: string }) => {
    createThreadMutation.mutate(data, {
      onSuccess: () => setShowNewThread(false),
    });
  };

  const handleFlag = async (postId: number) => {
    try {
      await flagPost(postId);
    } catch {
      // silently fail — user may not have permission
    }
  };

  if (selectedThreadId && threadDetail) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Button
          component={Link}
          href={`/courses/${courseId}/forum`}
          startIcon={<ArrowBackIcon />}
          sx={{ mb: 2 }}
        >
          Volver al foro
        </Button>

        {threadLoading ? (
          <Box sx={{ textAlign: "center", py: 4 }}><CircularProgress /></Box>
        ) : (
          <>
            <ThreadDetail
              thread={threadDetail}
              onUpvote={(replyId) => upvoteMutation.mutate(replyId)}
              onFlag={handleFlag}
            />
            <ReplyForm
              onSubmit={(data) => createReplyMutation.mutate(data)}
              isPending={createReplyMutation.isPending}
            />
          </>
        )}
      </Container>
    );
  }

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

      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
        <Typography variant="h4" component="h1">
          Foro
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setShowNewThread(true)}
        >
          Nuevo tema
        </Button>
      </Box>

      {threadsError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Error al cargar los temas.
        </Alert>
      )}

      {threadsLoading ? (
        <Box sx={{ textAlign: "center", py: 4 }}><CircularProgress /></Box>
      ) : (
        <ThreadList
          threads={allThreads}
          courseId={courseId}
          hasNextPage={hasNextPage}
          onLoadMore={() => fetchNextPage()}
          isLoadingMore={isFetchingNextPage}
        />
      )}

      <Dialog
        open={showNewThread}
        onClose={() => setShowNewThread(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Nuevo tema</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <ThreadForm
            onSubmit={handleCreateThread}
            isPending={createThreadMutation.isPending}
          />
        </DialogContent>
      </Dialog>
    </Container>
  );
}
