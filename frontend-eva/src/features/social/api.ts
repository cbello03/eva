import { apiClient } from "@/lib/api-client";

// ── Types ────────────────────────────────────────────────────────────

export interface ThreadAuthor {
  id: number;
  display_name: string;
}

export interface ForumThread {
  id: number;
  course_id: number;
  author: ThreadAuthor;
  title: string;
  body: string;
  is_hidden: boolean;
  reply_count: number;
  last_activity_at: string;
  created_at: string;
}

export interface PaginatedThreads {
  count: number;
  next_offset: number | null;
  results: ForumThread[];
}

export interface ForumReply {
  id: number;
  thread_id: number;
  author: ThreadAuthor;
  body: string;
  is_hidden: boolean;
  upvote_count: number;
  has_upvoted: boolean;
  created_at: string;
}

export interface ThreadDetail extends ForumThread {
  replies: ForumReply[];
}

export interface ChatMessage {
  id: number;
  course_id: number;
  author: ThreadAuthor;
  content: string;
  sent_at: string;
}

// ── API functions ────────────────────────────────────────────────────

/** List forum threads for a course (paginated). */
export async function listThreads(
  courseId: number,
  offset = 0,
  limit = 20,
): Promise<PaginatedThreads> {
  const response = await apiClient.get<PaginatedThreads>(
    `/courses/${courseId}/forum/threads`,
    { params: { offset, limit } },
  );
  return response.data;
}

/** Create a new forum thread. */
export async function createThread(
  courseId: number,
  data: { title: string; body: string },
): Promise<ForumThread> {
  const response = await apiClient.post<ForumThread>(
    `/courses/${courseId}/forum/threads`,
    data,
  );
  return response.data;
}

/** Get a thread with its replies. */
export async function getThread(threadId: number): Promise<ThreadDetail> {
  const response = await apiClient.get<ThreadDetail>(
    `/forum/threads/${threadId}`,
  );
  return response.data;
}

/** Reply to a thread. */
export async function createReply(
  threadId: number,
  data: { body: string },
): Promise<ForumReply> {
  const response = await apiClient.post<ForumReply>(
    `/forum/threads/${threadId}/replies`,
    data,
  );
  return response.data;
}

/** Flag a post (Teacher/Admin only). */
export async function flagPost(postId: number): Promise<void> {
  await apiClient.post(`/forum/posts/${postId}/flag`);
}

/** Toggle upvote on a reply. */
export async function toggleUpvote(replyId: number): Promise<ForumReply> {
  const response = await apiClient.post<ForumReply>(
    `/forum/replies/${replyId}/upvote`,
  );
  return response.data;
}
