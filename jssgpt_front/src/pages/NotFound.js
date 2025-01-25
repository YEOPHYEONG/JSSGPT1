import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { Link } from 'react-router-dom';

/**
 * 404 Not Found Page
 */
const NotFound = () => {
  return (
    <Box sx={{ textAlign: 'center', mt: 4 }}>
      <Typography variant="h3" gutterBottom>
        404 - Page Not Found
      </Typography>
      <Typography variant="body1" sx={{ mt: 2, mb: 4 }}>
        Sorry, the page you're looking for doesn't exist.
      </Typography>
      <Button variant="contained" color="primary" component={Link} to="/">
        Go Back to Home
      </Button>
    </Box>
  );
};

export default NotFound;
