import React from 'react';
import { List, ListItem, ListItemText, Typography, Box } from '@mui/material';

/**
 * STAR Experience List Component
 * @param {array} stars - Array of STAR experiences
 */
const StarList = ({ stars }) => {
  if (!stars || stars.length === 0) {
    return (
      <Typography variant="body2" color="textSecondary">
        No STAR experiences available.
      </Typography>
    );
  }

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Your STAR Experiences
      </Typography>
      <List>
        {stars.map((star) => (
          <ListItem key={star.id} sx={{ borderBottom: '1px solid #ddd' }}>
            <ListItemText
              primary={star.title}
              secondary={
                <>
                  <Typography variant="body2" color="textSecondary">
                    {star.description}
                  </Typography>
                </>
              }
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default StarList;
