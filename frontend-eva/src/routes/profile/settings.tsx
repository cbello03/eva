import React from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Typography, Box, Card, Grid, Switch, Select, MenuItem, FormControl, Button, Divider, Alert, Snackbar } from '@mui/material';
import { useTranslation } from 'react-i18next';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import LanguageIcon from '@mui/icons-material/Language';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import SaveIcon from '@mui/icons-material/Save';
import { motion } from 'framer-motion';

export const Route = createFileRoute('/profile/settings')({
  component: Settings,
});

function Settings() {
  const { t, i18n } = useTranslation();
  const [language, setLanguage] = React.useState(i18n.language || 'es');
  const [darkMode, setDarkMode] = React.useState(true);
  const [showSavedMsg, setShowSavedMsg] = React.useState(false);

  const handleLanguageChange = (event: any) => {
    const newLang = event.target.value;
    setLanguage(newLang);
    i18n.changeLanguage(newLang);
  };

  const handleSave = () => {
    // Save to local storage or API
    setShowSavedMsg(true);
    setTimeout(() => setShowSavedMsg(false), 3000);
  };

  return (
    <Box sx={{ pb: 6, maxWidth: 800, mx: 'auto', mt: 4 }}>
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: "easeOut" }}>
        <Card sx={{ 
          p: { xs: 3, md: 5 }, 
          borderRadius: 5, 
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(255,255,255,0.05)',
          boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 2 }}>
            <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: 'rgba(99,102,241,0.1)', color: '#818cf8' }}>
              <SettingsIcon sx={{ fontSize: 32 }} />
            </Box>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: 'white' }}>
                {t('settings_title')}
              </Typography>
              <Typography variant="body1" sx={{ color: '#94a3b8' }}>
                {t('settings_subtitle')}
              </Typography>
            </Box>
          </Box>
          
          <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)', my: 4 }} />

          <Grid container spacing={4}>
            {/* Language Settings */}
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: 'rgba(56,189,248,0.1)', color: '#38bdf8' }}>
                  <LanguageIcon />
                </Box>
                <Box sx={{ width: '100%' }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                    {t('settings_language')}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#94a3b8', mb: 2 }}>
                    {t('settings_language_desc')}
                  </Typography>
                  <FormControl fullWidth variant="outlined" sx={{
                    '& .MuiOutlinedInput-root': {
                      color: 'white',
                      background: 'rgba(15,23,42,0.6)',
                      borderRadius: 3,
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.1)' },
                      '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                      '&.Mui-focused fieldset': { borderColor: '#38bdf8' },
                    },
                    '& .MuiSelect-icon': { color: 'white' }
                  }}>
                    <Select value={language} onChange={handleLanguageChange}>
                      <MenuItem value="es">Español</MenuItem>
                      <MenuItem value="en">English</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              </Box>
            </Grid>

            {/* Theme Settings */}
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: 'rgba(236,72,153,0.1)', color: '#f472b6' }}>
                  <DarkModeIcon />
                </Box>
                <Box sx={{ width: '100%' }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                    {t('settings_theme')}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#94a3b8', mb: 2 }}>
                    {t('settings_theme_desc')}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2, borderRadius: 3, bgcolor: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <Typography sx={{ color: 'white', fontWeight: 600 }}>Modo Oscuro</Typography>
                    <Switch checked={darkMode} onChange={(e) => setDarkMode(e.target.checked)} sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': { color: '#f472b6' },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#f472b6' }
                    }} />
                  </Box>
                </Box>
              </Box>
            </Grid>

          </Grid>

          <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)', my: 4 }} />

          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                variant="contained"
                onClick={handleSave}
                startIcon={<SaveIcon />}
                sx={{
                  py: 1.5, px: 4,
                  borderRadius: 3,
                  fontWeight: 700,
                  fontSize: '1rem',
                  textTransform: 'none',
                  background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                  boxShadow: '0 8px 16px rgba(99,102,241,0.3)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #4f46e5 0%, #9333ea 100%)',
                    boxShadow: '0 12px 20px rgba(99,102,241,0.5)',
                  }
                }}
              >
                {t('settings_save')}
              </Button>
            </motion.div>
          </Box>
        </Card>
      </motion.div>

      <Snackbar open={showSavedMsg} autoHideDuration={3000} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert severity="success" sx={{ width: '100%', borderRadius: 3, fontWeight: 600, bgcolor: '#10b981', color: 'white', alignItems: 'center' }}>
          {t('settings_saved')}
        </Alert>
      </Snackbar>
    </Box>
  );
}

// Needed because I used SettingsIcon but imported AutoAwesomeIcon above instead
import SettingsIcon from '@mui/icons-material/Settings';
