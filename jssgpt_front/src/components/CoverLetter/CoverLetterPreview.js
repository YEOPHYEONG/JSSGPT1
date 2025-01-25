import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

/**
 * Cover Letter Preview Component
 * @param {string} content - Content of the cover letter to preview
 */
const CoverLetterPreview = ({ content }) => {
  return (
    <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Preview Your Cover Letter
      </Typography>
      <Box
        dangerouslySetInnerHTML={{ __html: content }}
        sx={{ mt: 2, whiteSpace: 'pre-wrap' }}
      />
    </Paper>
  );
};

export default CoverLetterPreview;
