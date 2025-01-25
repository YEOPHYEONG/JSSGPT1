import React from 'react';
import { MenuItem, Select, FormControl, InputLabel, Box, Typography } from '@mui/material';

/**
 * STAR Experience Selector Component
 * @param {array} stars - Array of STAR experiences
 * @param {string} selectedStar - Currently selected STAR experience ID
 * @param {function} onSelect - Callback function to handle selection
 */
const StarSelector = ({ stars, selectedStar, onSelect }) => {
  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Select a STAR Experience
      </Typography>
      <FormControl fullWidth>
        <InputLabel id="star-selector-label">STAR Experience</InputLabel>
        <Select
          labelId="star-selector-label"
          value={selectedStar}
          onChange={(e) => onSelect(e.target.value)}
          label="STAR Experience"
        >
          {stars.map((star) => (
            <MenuItem key={star.id} value={star.id}>
              {star.title}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
};

export default StarSelector;
