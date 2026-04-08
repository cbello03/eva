"use client";

import { useMemo, useState } from "react";
import {
  Container,
  Typography,
  TextField,
  InputAdornment,
  ToggleButtonGroup,
  ToggleButton,
  Box,
  CircularProgress,
  Alert,
} from "@mui/material";
import { Search as SearchIcon } from "@mui/icons-material";
import { useCourses, useEnrollments } from "@/features/courses/hooks";
import CourseList from "@/features/courses/components/CourseList";

type Filter = "all" | "enrolled" | "available";

export default function CoursesPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");

  const { data: courses, isLoading: coursesLoading, error: coursesError } = useCourses();
  const { data: enrollments, isLoading: enrollmentsLoading } = useEnrollments();

  const enrolledCourseIds = useMemo(
    () => new Set((enrollments ?? []).filter((e) => e.is_active).map((e) => e.course_id)),
    [enrollments],
  );

  const filteredCourses = useMemo(() => {
    if (!courses) return [];

    let result = courses;

    // Apply text search
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (c) =>
          c.title.toLowerCase().includes(q) ||
          c.description.toLowerCase().includes(q),
      );
    }

    // Apply enrollment filter
    if (filter === "enrolled") {
      result = result.filter((c) => enrolledCourseIds.has(c.id));
    } else if (filter === "available") {
      result = result.filter((c) => !enrolledCourseIds.has(c.id));
    }

    return result;
  }, [courses, search, filter, enrolledCourseIds]);

  const isLoading = coursesLoading || enrollmentsLoading;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Cursos
      </Typography>

      <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
        <TextField
          placeholder="Buscar cursos…"
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            },
          }}
          sx={{ minWidth: 260 }}
        />

        <ToggleButtonGroup
          value={filter}
          exclusive
          onChange={(_, v: Filter | null) => { if (v) setFilter(v); }}
          size="small"
        >
          <ToggleButton value="all">Todos</ToggleButton>
          <ToggleButton value="enrolled">Inscritos</ToggleButton>
          <ToggleButton value="available">Disponibles</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {coursesError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Error al cargar los cursos. Por favor, inténtalo de nuevo.
        </Alert>
      )}

      {isLoading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <CourseList
          courses={filteredCourses}
          enrollments={enrollments ?? []}
        />
      )}
    </Container>
  );
}
