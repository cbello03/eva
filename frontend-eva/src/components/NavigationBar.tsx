"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Badge,
  Box,
  Menu,
  MenuItem,
  Avatar,
  Divider,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import {
  School as SchoolIcon,
  Dashboard as DashboardIcon,
  Leaderboard as LeaderboardIcon,
  Notifications as NotificationsIcon,
  Person as PersonIcon,
  Logout as LogoutIcon,
  Build as BuildIcon,
} from "@mui/icons-material";
import { useAuth } from "@/features/auth/hooks";
import { useLogout } from "@/features/auth/hooks";

export default function NavigationBar() {
  const { user, isAuthenticated } = useAuth();
  const logoutMutation = useLogout();
  const pathname = usePathname();
  const router = useRouter();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleMenuClose();
    logoutMutation.mutate(undefined, {
      onSuccess: () => router.push("/login"),
    });
  };

  const isActive = (path: string) => pathname === path || pathname.startsWith(path + "/");

  const isTeacher = user?.role === "teacher" || user?.role === "admin";

  return (
    <AppBar position="sticky" color="default" elevation={1} sx={{ bgcolor: "background.paper" }}>
      <Toolbar sx={{ gap: 1 }}>
        <Typography
          variant="h6"
          component={Link}
          href={isAuthenticated ? "/dashboard" : "/"}
          sx={{
            fontFamily: "'Fraunces', serif",
            fontWeight: 700,
            color: "primary.main",
            textDecoration: "none",
            mr: 3,
          }}
        >
          EVA
        </Typography>

        {isAuthenticated && (
          <>
            <Box sx={{ display: "flex", gap: 0.5, flexGrow: 1 }}>
              <Button
                component={Link}
                href="/dashboard"
                startIcon={<DashboardIcon />}
                color={isActive("/dashboard") ? "primary" : "inherit"}
                size="small"
              >
                Dashboard
              </Button>
              <Button
                component={Link}
                href="/courses"
                startIcon={<SchoolIcon />}
                color={isActive("/courses") ? "primary" : "inherit"}
                size="small"
              >
                Courses
              </Button>
              {isTeacher && (
                <Button
                  component={Link}
                  href="/teacher"
                  startIcon={<BuildIcon />}
                  color={isActive("/teacher") ? "primary" : "inherit"}
                  size="small"
                >
                  Teach
                </Button>
              )}
            </Box>

            <IconButton size="small" aria-label="notifications">
              <Badge badgeContent={0} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>

            <IconButton onClick={handleMenuOpen} size="small" aria-label="account menu">
              <Avatar
                sx={{ width: 32, height: 32, bgcolor: "primary.main", fontSize: 14 }}
              >
                {user?.display_name?.charAt(0).toUpperCase() ?? "U"}
              </Avatar>
            </IconButton>

            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
              transformOrigin={{ horizontal: "right", vertical: "top" }}
              anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
            >
              <MenuItem disabled>
                <ListItemText
                  primary={user?.display_name}
                  secondary={user?.email}
                />
              </MenuItem>
              <Divider />
              <MenuItem
                component={Link}
                href="/profile"
                onClick={handleMenuClose}
              >
                <ListItemIcon><PersonIcon fontSize="small" /></ListItemIcon>
                <ListItemText>Profile</ListItemText>
              </MenuItem>
              <MenuItem onClick={handleLogout}>
                <ListItemIcon><LogoutIcon fontSize="small" /></ListItemIcon>
                <ListItemText>Log out</ListItemText>
              </MenuItem>
            </Menu>
          </>
        )}

        {!isAuthenticated && (
          <Box sx={{ display: "flex", gap: 1, ml: "auto" }}>
            <Button component={Link} href="/login" variant="text">
              Log in
            </Button>
            <Button component={Link} href="/register" variant="contained">
              Sign up
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}
