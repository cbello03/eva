import { apiClient } from "@/lib/api-client";

// ── Types ────────────────────────────────────────────────────────────

export interface RubricCriterion {
  name: string;
  max_score: number;
  description: string;
}

export interface Project {
  id: number;
  course_id: number;
  teacher_id: number;
  title: string;
  description: string;
  rubric: RubricCriterion[];
  submission_deadline: string;
  peer_review_enabled: boolean;
  peer_reviewers_count: number;
  created_at: string;
}

export interface SubmissionFile {
  id: number;
  filename: string;
  file_size: number;
}

export interface ProjectSubmission {
  id: number;
  project_id: number;
  student_id: number;
  description: string;
  files: SubmissionFile[];
  is_late: boolean;
  submitted_at: string;
}

export interface ProjectReview {
  id: number;
  submission_id: number;
  reviewer_id: number;
  reviewer_name: string;
  review_type: "teacher" | "peer";
  scores: Record<string, number>;
  feedback: string;
  is_complete: boolean;
  created_at: string;
}

// ── API functions ────────────────────────────────────────────────────

/** Get project detail. */
export async function getProject(projectId: number): Promise<Project> {
  const response = await apiClient.get<Project>(`/projects/${projectId}`);
  return response.data;
}

/** Submit a project (multipart form data). */
export async function submitProject(
  projectId: number,
  data: { description: string; files: File[] },
): Promise<ProjectSubmission> {
  const formData = new FormData();
  formData.append("description", data.description);
  for (const file of data.files) {
    formData.append("files", file);
  }
  const response = await apiClient.post<ProjectSubmission>(
    `/projects/${projectId}/submit`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

/** Submit a review for a submission. */
export async function submitReview(
  submissionId: number,
  data: { scores: Record<string, number>; feedback: string },
): Promise<ProjectReview> {
  const response = await apiClient.post<ProjectReview>(
    `/submissions/${submissionId}/review`,
    data,
  );
  return response.data;
}

/** Get reviews for a submission. */
export async function getReviews(
  submissionId: number,
): Promise<ProjectReview[]> {
  const response = await apiClient.get<ProjectReview[]>(
    `/submissions/${submissionId}/reviews`,
  );
  return response.data;
}
