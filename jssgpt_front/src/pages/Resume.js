import React, { useState } from 'react';
import { Box, Typography } from '@mui/material';
import UploadForm from '../components/ResumeUpload/UploadForm';
import UploadedResume from '../components/ResumeUpload/UploadedResume';

/**
 * Resume Page
 */
const Resume = () => {
  const [resumeData, setResumeData] = useState(null);

  const handleUpload = (data) => {
    setResumeData(data);
  };

  const handleDelete = () => {
    setResumeData(null);
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Resume Management
      </Typography>
      <UploadForm onUpload={handleUpload} />
      <UploadedResume resumeData={resumeData} onDelete={handleDelete} />
    </Box>
  );
};

export default Resume;
