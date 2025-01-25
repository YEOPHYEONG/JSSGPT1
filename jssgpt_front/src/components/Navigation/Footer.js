import React from 'react';
import { Box, Typography } from '@mui/material';

/**
 * Footer Component
 */
const Footer = () => {
  return (
    <Box
      component="footer"
      sx={{
        mt: 4,
        py: 2,
        textAlign: 'center',
        backgroundColor: '#f1f1f1',
        borderTop: '1px solid #ddd',
      }}
    >
      <Typography variant="body2" color="textSecondary">
        &copy; {new Date().getFullYear()} Cover Letter Helper. All rights reserved.
      </Typography>
    </Box>
  );
};

export default Footer;
