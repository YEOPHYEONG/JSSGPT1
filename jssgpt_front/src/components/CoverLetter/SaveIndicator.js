import React from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';

/**
 * Save Indicator Component
 * @param {boolean} isSaving - Whether the content is currently being saved
 */
const SaveIndicator = ({ isSaving }) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
      {isSaving ? (
        <>
          <CircularProgress size={20} sx={{ mr: 1 }} />
          <Typography variant="body2">Saving...</Typography>
        </>
      ) : (
        <Typography variant="body2" color="textSecondary">
          All changes saved.
        </Typography>
      )}
    </Box>
  );
};

export default SaveIndicator;
