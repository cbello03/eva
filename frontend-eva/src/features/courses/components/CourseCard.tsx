"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  LinearProgress,
} from "@mui/material";
import {
  School as SchoolIcon,
  CheckCircle as CheckCircleIcon,
} from "@mui/icons-material";
import type { CourseListItem, Enrollment } from "../types";

interface CourseCardProps {
  course: CourseListItem;
  enrollment?: Enrollment;
}

export default function CourseCard({ course, enrollment }: CourseCardProps) {
  const isEnrolled = enrollment?.is_active;
  const progress = enrollment?.progress_percentage ?? 0;

  return (
    <Card
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        transition: "box-shadow 0.2s",
        "&:hover": { boxShadow: "0 4px 20px rgba(0,0,0,0.12)" },
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
          <SchoolIcon color="primary" fontSize="small" />
          <Typography variant="h6" component="h2" noWrap>
            {course.title}
          </Typography>
        </Box>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2,
            display: "-webkit-box",
            WebkitLineClamp: 3,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {course.description}
        </Typography>

        {isEnrolled && (
          <Box sx={{ mt: "auto" }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
              <Chip
                icon={<CheckCircleIcon />}
                label="Enrolled"
                size="small"
                color="secondary"
                variant="outlined"
              />
              <Typography variant="caption" color="text.secondary">
                {Math.round(progress)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ borderRadius: 4, height: 6 }}
            />
          </Box>
        )}
      </CardContent>

      <CardActions sx={{ px: 2, pb: 2 }}>
        <Button
          component={Link}
          href={`/courses/${course.id}`}
          size="small"
          variant={isEnrolled ? "outlined" : "contained"}
          fullWidth
        >
          {isEnrolled ? "Continue" : "View Course"}
        </Button>
      </CardActions>
    </Card>
  );
}
