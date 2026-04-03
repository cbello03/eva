import React, { useState } from 'react';
import { Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Typography, Avatar, InputBase, IconButton, Badge, Menu, MenuItem, useTheme, useMediaQuery } from '@mui/material';
import { Link, Outlet, useLocation } from '@tanstack/react-router';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ClassIcon from '@mui/icons-material/Class';
import AssignmentIcon from '@mui/icons-material/Assignment';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import PeopleIcon from '@mui/icons-material/People';
import SettingsIcon from '@mui/icons-material/Settings';
import SearchIcon from '@mui/icons-material/Search';
import NotificationsIcon from '@mui/icons-material/Notifications';
import MenuIcon from '@mui/icons-material/Menu';

import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { useNavigate } from '@tanstack/react-router';
import { useAuthStore } from '../features/auth/store';

const drawerWidth = 260;

export function Layout() {
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const menuItems = [
    { text: t('dashboard_title'), icon: <DashboardIcon />, path: '/dashboard' },
    { text: t('my_courses'), icon: <ClassIcon />, path: '/courses' },
    { text: t('assignments'), icon: <AssignmentIcon />, path: '/projects' },
    { text: t('achievements'), icon: <EmojiEventsIcon />, path: '/profile' },
    { text: t('community'), icon: <PeopleIcon />, path: '/teacher' },
    { text: t('settings'), icon: <SettingsIcon />, path: '/profile/settings' },
  ];



  const handleUserClick = (event: React.MouseEvent<HTMLDivElement>) => setUserMenuAnchor(event.currentTarget);
  const handleUserClose = () => setUserMenuAnchor(null);

  const handleLogout = () => {
    handleUserClose();
    logout();
    navigate({ to: '/login' });
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawerContent = (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 5, px: 2, pt: 3 }}>
        <Box sx={{
          width: 32, height: 32, borderRadius: 2, 
          background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', mr: 1.5
        }}>
          <Typography variant="h6" sx={{ color: 'white', fontWeight: 800 }}>E</Typography>
        </Box>
        <Typography variant="h6" sx={{ color: '#fff', fontWeight: 700, lineHeight: 1.1 }}>
          Eva - Next Gen<br/>
          <span style={{ color: '#ec4899' }}>Learning</span>
        </Typography>
      </Box>

      <List>
        {menuItems.map((item, index) => {
          const isActive = location.pathname.startsWith(item.path);
          return (
            <motion.div key={item.text} initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: index * 0.05 }}>
              <ListItem disablePadding sx={{ mb: 1 }}>
                <ListItemButton
                  component={Link}
                  to={item.path}
                  onClick={() => { if (isMobile) setMobileOpen(false); }}
                  sx={{
                    borderRadius: '12px',
                    transition: 'all 0.2s',
                    background: isActive ? 'linear-gradient(90deg, rgba(99,102,241,0.1) 0%, transparent 100%)' : 'transparent',
                    borderLeft: isActive ? '3px solid #6366f1' : '3px solid transparent',
                    color: isActive ? '#f8fafc' : '#94a3b8',
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.03)',
                      color: '#fff',
                    }
                  }}
                >
                  <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.text} primaryTypographyProps={{ fontWeight: isActive ? 600 : 500 }} />
                </ListItemButton>
              </ListItem>
            </motion.div>
          );
        })}
      </List>
    </>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      
      {/* Mobile Sidebar */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }} 
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth, bgcolor: '#0f172a', borderRight: '1px solid rgba(255,255,255,0.05)', px: 2 }
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Desktop Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box', bgcolor: '#0f172a', borderRight: '1px solid rgba(255,255,255,0.05)', py: 3, px: 2 },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, p: { xs: 2, md: 4 }, overflowX: 'hidden', width: { xs: '100%', md: `calc(100% - ${drawerWidth}px)` } }}>
        {/* Header */}
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'stretch', md: 'center' }, gap: 2, mb: 5 }}>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ display: { md: 'none' }, color: 'white' }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                {t('hello', { name: 'Alex' })}
              </motion.div>
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: { xs: 'space-between', md: 'flex-end' }, gap: 2 }}>
            <Box sx={{
              display: { xs: 'none', sm: 'flex' }, alignItems: 'center', bgcolor: '#1e293b',
              borderRadius: '20px', px: 2, py: 0.5, border: '1px solid rgba(255,255,255,0.05)'
            }}>
              <SearchIcon sx={{ color: '#94a3b8', fontSize: 20, mr: 1 }} />
              <InputBase placeholder={t('search_placeholder')} sx={{ color: 'white' }} />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>


              <IconButton sx={{ display: { xs: 'none', sm: 'flex' }, bgcolor: '#1e293b', border: '1px solid rgba(255,255,255,0.05)' }}>
                <Badge variant="dot" color="error">
                  <NotificationsIcon sx={{ color: '#94a3b8', fontSize: 20 }} />
                </Badge>
              </IconButton>
            </Box>

            <Box 
              onClick={handleUserClick}
              sx={{ display: 'flex', alignItems: 'center', gap: 1, cursor: 'pointer', p: 0.5, pr: { xs: 1, sm: 2 }, borderRadius: 5, bgcolor: '#1e293b', border: '1px solid rgba(255,255,255,0.05)', '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' } }}>
              <Avatar src="https://i.pravatar.cc/150?img=11" sx={{ width: 32, height: 32 }} />
              <Typography variant="body2" sx={{ fontWeight: 600, display: { xs: 'none', sm: 'block' } }}>Alex Thompson ▼</Typography>
            </Box>

            <Menu 
              anchorEl={userMenuAnchor} 
              open={Boolean(userMenuAnchor)} 
              onClose={handleUserClose}
              PaperProps={{
                sx: {
                  mt: 1,
                  bgcolor: '#1e293b',
                  color: 'white',
                  border: '1px solid rgba(255,255,255,0.1)',
                  minWidth: 150
                }
              }}
            >
              <MenuItem component={Link} to="/profile" onClick={handleUserClose} sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' } }}>
                 {t('view_profile')}
              </MenuItem>
              <MenuItem onClick={handleLogout} sx={{ color: '#f43f5e', '&:hover': { bgcolor: 'rgba(244,63,94,0.1)' } }}>
                 {t('logout')}
              </MenuItem>
            </Menu>
          </Box>
        </Box>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
           <Outlet />
        </motion.div>
      </Box>
    </Box>
  );
}
