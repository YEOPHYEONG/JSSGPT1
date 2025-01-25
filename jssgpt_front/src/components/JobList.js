import React from 'react';
import { Box, Typography, List, ListItem, ListItemText } from '@mui/material';

const JobList = ({ jobs }) => {
  return (
    <Box sx={{ p: 2, overflowY: 'auto', height: 'calc(100vh - 64px)' }}>
      <Typography variant="h6" gutterBottom>
        채용 공고
      </Typography>
      <List>
        {jobs.map((job) => (
          <ListItem key={job.id} sx={{ borderBottom: '1px solid #ddd' }}>
            <ListItemText primary={job.company} secondary={job.date} />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default JobList;
