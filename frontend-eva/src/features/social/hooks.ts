import {
  useMutation,
  useQuery,
  useQueryClient,
  useInfiniteQuery,
} from "@tanstack/react-query";
import * as socialApi from "./api";
import type { PaginatedThreads } from "./api";

// ── Query keys ───────────────────────────────────────────────────────

export const socialKeys = {
  threads: (courseId: number) => ["social", "threads", courseId] as const,
  thread: (threadId: number) => ["social", "thread", threadId] as const,
};

// ── useForumThreads: paginated thread list for a course ──────────────

export function useForumThreads(courseId: number, limit = 20) {
  return useInfiniteQuery({
    queryKey: socialKeys.threads(courseId),
    queryFn: ({ pageParam = 0 }) =>
      socialApi.listThreads(courseId, pageParam, limit),
    initialPageParam: 0,
    getNextPageParam: (lastPage: PaginatedThreads) =>
      lastPage.next_offset ?? undefined,
    enabled: courseId > 0,
  });
}

// ── useThread: single thread with replies ────────────────────────────

export function useThread(threadId: number) {
  return useQuery({
    queryKey: socialKeys.thread(threadId),
    queryFn: () => socialApi.getThread(threadId),
    enabled: threadId > 0,
  });
}

// ── useCreateThread: create a new forum thread ───────────────────────

export function useCreateThread(courseId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { title: string; body: string }) =>
      socialApi.createThread(courseId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: socialKeys.threads(courseId),
      });
    },
  });
}

// ── useCreateReply: reply to a thread ────────────────────────────────

export function useCreateReply(threadId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { body: string }) =>
      socialApi.createReply(threadId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: socialKeys.thread(threadId),
      });
    },
  });
}

// ── useUpvote: toggle upvote on a reply ──────────────────────────────

export function useUpvote(threadId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: socialApi.toggleUpvote,
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: socialKeys.thread(threadId),
      });
    },
  });
}
