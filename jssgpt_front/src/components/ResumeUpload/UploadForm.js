import React, { useState } from 'react';
import { Box, Button, Typography } from '@mui/material';

/**
 * Resume Upload Form Component
 * @param {function} onUpload - Callback function triggered after successful upload
 */
const UploadForm = ({ onUpload }) => {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('resume', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      onUpload(data); // Pass response data to parent component
      setFile(null); // Reset file input after successful upload
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2, p: 3, border: '1px solid #ddd', borderRadius: 2 }}>
      <Typography variant="h6" gutterBottom>
        Upload Your Resume
      </Typography>
      <input
        type="file"
        onChange={handleFileChange}
        accept=".pdf,.doc,.docx"
        style={{ display: 'block', marginBottom: '16px' }}
      />
      <Button
        type="submit"
        color="primary"
        variant="contained"
        disabled={!file}
      >
        Upload
      </Button>
    </Box>
  );
};

export default UploadForm;
