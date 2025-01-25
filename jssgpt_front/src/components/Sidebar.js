import React from 'react';
import { Box, Typography } from '@mui/material';

const Sidebar = () => {
  return (
    <Box sx={{ p: 2, borderLeft: '1px solid #ddd', height: 'calc(100vh - 64px)' }}>
      <Typography variant="h6" gutterBottom>
        인기 기업
      </Typography>
      <Typography>한화시멘트</Typography>
      <Typography>카카오</Typography>
      <Typography>네이버</Typography>
    </Box>
  );
};

export default Sidebar;
