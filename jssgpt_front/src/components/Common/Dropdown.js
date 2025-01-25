import React from 'react';
import { MenuItem, Select, FormControl, InputLabel } from '@mui/material';

/**
 * Reusable Dropdown Component
 * @param {string} label - Label for the dropdown
 * @param {array} options - Array of options [{label: string, value: any}]
 * @param {any} value - The selected value
 * @param {function} onChange - Function to handle dropdown value change
 */
const Dropdown = ({ label, options, value, onChange }) => {
  return (
    <FormControl fullWidth>
      <InputLabel>{label}</InputLabel>
      <Select value={value} onChange={onChange} label={label}>
        {options.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default Dropdown;
