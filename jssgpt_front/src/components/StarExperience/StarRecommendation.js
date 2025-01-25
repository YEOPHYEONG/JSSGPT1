import React from 'react';
import { Box, Typography, Button } from '@mui/material';

/**
 * STAR Experience Recommendation Component
 * @param {object} recommendation - AI recommendation result
 * @param {function} onAccept - Callback function when user accepts the recommendation
 */
const StarRecommendation = ({ recommendation, onAccept }) => {
  if (!recommendation) {
    return (
      <Typography variant="body2" color="textSecondary">
        No recommendations available.
      </Typography>
    );
  }

  return (
    <Box sx={{ mt: 3, p: 3, border: '1px solid #ddd', borderRadius: 2 }}>
      <Typography variant="h6" gutterBottom>
        Recommended STAR Experience
      </Typography>
      <Typography variant="body1" gutterBottom>
        {recommendation.title}
      </Typography>
      <Typography variant="body2" color="textSecondary">
        {recommendation.description}
      </Typography>
      <Button
        sx={{ mt: 2 }}
        variant="contained"
        color="primary"
        onClick={onAccept}
      >
        Accept Recommendation
      </Button>
    </Box>
  );
};

export default StarRecommendation;
