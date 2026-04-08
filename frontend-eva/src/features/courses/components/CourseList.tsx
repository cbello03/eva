"use client";

import { Grid, Typography, Box } from "@mui/material";
import type { CourseListItem, Enrollment } from "../types";
import CourseCard from "./CourseCard";

interface CourseListProps {
  courses: CourseListItem[];
  enrollments: Enrollment[];
}

export default function CourseList({ courses, enrollments }: CourseListProps) {
  const enrollmentMap = new Map(
    enrollments
      .filter((e) => e.is_active)
      .map((e) => [e.course_id, e]),
  );

  if (courses.length === 0) {
    return (
      <Box sx={{ textAlign: "center", py: 8 }}>
        <Typography variant="h6" color="text.secondary">
          No courses found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Try adjusting your search or filters.
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {courses.map((course) => (
        <Grid key={course.id} size={{ xs: 12, sm: 6, md: 4 }}>
          <CourseCard
            course={course}
            enrollment={enrollmentMap.get(course.id)}
          />
        </Grid>
      ))}
    </Grid>
  );
}
