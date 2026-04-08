"use client";

import {
  Container,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
} from "@mui/material";
import BarChartIcon from "@mui/icons-material/BarChart";
import EditIcon from "@mui/icons-material/Edit";
import Link from "next/link";
import { useCourses } from "@/features/courses/hooks";

export default function TeacherDashboardPage() {
  const { data: courses, isLoading, error } = useCourses();

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Failed to load courses.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Teacher Dashboard
      </Typography>

      {courses && courses.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          You don&apos;t have any courses yet.
        </Typography>
      ) : (
        <TableContainer component={Paper} variant="outlined">
          <Table aria-label="Teacher courses">
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Last Modified</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(courses ?? []).map((course) => (
                <TableRow key={course.id}>
                  <TableCell>{course.title}</TableCell>
                  <TableCell>
                    <Chip
                      label={course.status}
                      color={
                        course.status === "published" ? "success" : "default"
                      }
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    {new Date(course.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      component={Link}
                      href={`/teacher/courses/${course.id}/builder`}
                      size="small"
                      aria-label="Edit course"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      component={Link}
                      href={`/teacher/analytics/${course.id}`}
                      size="small"
                      aria-label="View analytics"
                    >
                      <BarChartIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Container>
  );
}
