import React, { useState } from 'react';
import { Box, Typography } from '@mui/material';
import CoverLetterEditor from '../components/CoverLetter/CoverLetterEditor';
import CoverLetterPreview from '../components/CoverLetter/CoverLetterPreview';
import SaveIndicator from '../components/CoverLetter/SaveIndicator';

/**
 * Cover Letter Page
 */
const CoverLetter = () => {
  const [content, setContent] = useState('<p>Start writing your cover letter here...</p>');
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = (newContent) => {
    setContent(newContent);
    setIsSaving(true);
    setTimeout(() => setIsSaving(false), 1000); // Simulate saving process
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Cover Letter Editor
      </Typography>
      <CoverLetterEditor initialContent={content} onSave={handleSave} />
      <SaveIndicator isSaving={isSaving} />
      <CoverLetterPreview content={content} />
    </Box>
  );
};

export default CoverLetter;
