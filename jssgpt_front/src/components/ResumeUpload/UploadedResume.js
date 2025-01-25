import React from 'react';
import { Box, Typography, Button } from '@mui/material';

/**
 * Uploaded Resume Display Component
 * @param {object} resumeData - Uploaded resume data to display
 * @param {function} onDelete - Callback function triggered when deleting the resume
 */
const UploadedResume = ({ resumeData, onDelete }) => {
  if (!resumeData) {
    return (
      <Typography variant="body2" color="textSecondary">
        No resume uploaded yet.
      </Typography>
    );
  }

  return (
    <Box sx={{ mt: 3, p: 2, border: '1px solid #ddd', borderRadius: 2 }}>
      <Typography variant="h6" gutterBottom>
        Uploaded Resume
      </Typography>
      <Typography variant="body1">File Name: {resumeData.fileName}</Typography>
      <Typography variant="body2" color="textSecondary">
        Upload Date: {new Date(resumeData.uploadDate).toLocaleString()}
      </Typography>
      <Button
        sx={{ mt: 2 }}
        color="error"
        variant="outlined"
        onClick={onDelete}
      >
        Delete Resume
      </Button>
    </Box>
  );
};

export default UploadedResume;
