import { apiClient } from "@/lib/api-client";
import type { Course, CourseListItem, Enrollment } from "./types";

/** List courses visible to the authenticated user. */
export async function listCourses(): Promise<CourseListItem[]> {
  const response = await apiClient.get<CourseListItem[]>("/courses");
  return response.data;
}

/** Get a single course with full unit/lesson hierarchy. */
export async function getCourse(courseId: number): Promise<Course> {
  const response = await apiClient.get<Course>(`/courses/${courseId}`);
  return response.data;
}

/** Enroll the current student in a course. */
export async function enrollInCourse(courseId: number): Promise<Enrollment> {
  const response = await apiClient.post<Enrollment>(
    `/courses/${courseId}/enroll`,
  );
  return response.data;
}

/** Unenroll the current student from a course. */
export async function unenrollFromCourse(courseId: number): Promise<void> {
  await apiClient.delete(`/courses/${courseId}/enroll`);
}

/** List the current student's enrollments with progress. */
export async function listEnrollments(): Promise<Enrollment[]> {
  const response = await apiClient.get<Enrollment[]>("/enrollments");
  return response.data;
}
