import React from 'react';
import { TextField } from '@mui/material';

/**
 * Reusable Text Input Component
 * @param {string} label - Label for the text input
 * @param {string} value - The input value
 * @param {function} onChange - Function to handle input value change
 * @param {boolean} multiline - If true, the input will be multiline
 * @param {object} props - Additional props for the MUI TextField
 */
const TextInput = ({ label, value, onChange, multiline = false, ...props }) => {
  return (
    <TextField
      label={label}
      value={value}
      onChange={onChange}
      multiline={multiline}
      fullWidth
      {...props}
    />
  );
};

export default TextInput;
