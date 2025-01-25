import React, { useState, useEffect } from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { Box, Typography } from '@mui/material';

/**
 * Cover Letter Editor Component
 * @param {string} initialContent - Initial content of the editor
 * @param {function} onSave - Function to handle saving the content
 */
const CoverLetterEditor = ({ initialContent = '', onSave }) => {
  const [content, setContent] = useState(initialContent);
  const [isSaving, setIsSaving] = useState(false);

  // Auto-save functionality
  useEffect(() => {
    const timer = setTimeout(() => {
      onSave(content);
      setIsSaving(true);
      setTimeout(() => setIsSaving(false), 1000); // Indicate save complete
    }, 2000);

    return () => clearTimeout(timer);
  }, [content, onSave]);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Edit Your Cover Letter
      </Typography>
      <ReactQuill
        value={content}
        onChange={setContent}
        style={{ height: '300px', marginBottom: '16px' }}
      />
      {isSaving && <Typography variant="body2">Saving...</Typography>}
    </Box>
  );
};

export default CoverLetterEditor;
