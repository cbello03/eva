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

export interface ChatbotAnswer {
  course_id: number;
  mode: "brief" | "detailed";
  question: string;
  answer: string;
}

export interface ChatbotTurn {
  role: "user" | "assistant";
  content: string;
}

interface ForumReplyApi {
  id: number;
  thread_id: number;
  author_id: number;
  author_display_name: string;
  body: string;
  is_hidden: boolean;
  upvote_count: number;
  created_at: string;
}

interface ForumThreadApi {
  id: number;
  course_id: number;
  author_id: number;
  author_display_name: string;
  title: string;
  body: string;
  is_hidden: boolean;
  last_activity_at: string;
  created_at: string;
  replies?: ForumReplyApi[];
}

interface PaginatedThreadsApi {
  count: number;
  next_offset: number | null;
  results: ForumThreadApi[];
}

const mapReply = (reply: ForumReplyApi): ForumReply => ({
  id: reply.id,
  thread_id: reply.thread_id,
  author: {
    id: reply.author_id,
    display_name: reply.author_display_name,
  },
  body: reply.body,
  is_hidden: reply.is_hidden,
  upvote_count: reply.upvote_count,
  has_upvoted: false,
  created_at: reply.created_at,
});

const mapThread = (thread: ForumThreadApi): ForumThread => ({
  id: thread.id,
  course_id: thread.course_id,
  author: {
    id: thread.author_id,
    display_name: thread.author_display_name,
  },
  title: thread.title,
  body: thread.body,
  is_hidden: thread.is_hidden,
  reply_count: thread.replies?.length ?? 0,
  last_activity_at: thread.last_activity_at,
  created_at: thread.created_at,
});

// ── API functions ────────────────────────────────────────────────────

/** List forum threads for a course (paginated). */
export async function listThreads(
  courseId: number,
  offset = 0,
  limit = 20,
): Promise<PaginatedThreads> {
  const response = await apiClient.get<PaginatedThreadsApi>(
    `/courses/${courseId}/forum/threads`,
    { params: { offset, limit } },
  );
  return {
    count: response.data.count,
    next_offset: response.data.next_offset,
    results: response.data.results.map(mapThread),
  };
}

/** Create a new forum thread. */
export async function createThread(
  courseId: number,
  data: { title: string; body: string },
): Promise<ForumThread> {
  const response = await apiClient.post<ForumThreadApi>(
    `/courses/${courseId}/forum/threads`,
    data,
  );
  return mapThread(response.data);
}

/** Get a thread with its replies. */
export async function getThread(threadId: number): Promise<ThreadDetail> {
  const response = await apiClient.get<ForumThreadApi>(
    `/forum/threads/${threadId}`,
  );
  const thread = response.data;
  return {
    ...mapThread(thread),
    replies: (thread.replies ?? []).map(mapReply),
  };
}

/** Reply to a thread. */
export async function createReply(
  threadId: number,
  data: { body: string },
): Promise<ForumReply> {
  const response = await apiClient.post<ForumReplyApi>(
    `/forum/threads/${threadId}/replies`,
    data,
  );
  return mapReply(response.data);
}

/** Flag a post (Teacher/Admin only). */
export async function flagPost(postId: number): Promise<void> {
  await apiClient.post(`/forum/posts/${postId}/flag`);
}

/** Toggle upvote on a reply. */
export async function toggleUpvote(replyId: number): Promise<ForumReply> {
  const response = await apiClient.post<ForumReplyApi>(
    `/forum/replies/${replyId}/upvote`,
  );
  return mapReply(response.data);
}

/** Ask a question to the course-scoped chatbot. */
export async function askCourseChatbot(
  courseId: number,
  question: string,
  mode: "brief" | "detailed" = "brief",
  history: ChatbotTurn[] = [],
): Promise<ChatbotAnswer> {
  const response = await apiClient.post<ChatbotAnswer>(
    `/courses/${courseId}/chatbot/ask`,
    { question, mode, history },
  );
  return response.data;
}
