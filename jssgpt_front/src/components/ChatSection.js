import React from 'react';
import { Box, Typography, Button } from '@mui/material';

const ChatSection = () => {
  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 0,
        right: 0,
        width: '300px',
        border: '1px solid #ddd',
        borderRadius: '8px 8px 0 0',
        backgroundColor: '#fff',
        p: 2,
      }}
    >
      <Typography variant="h6" gutterBottom>
        채팅
      </Typography>
      <Button variant="contained" color="primary" fullWidth>
        채팅 시작
      </Button>
    </Box>
  );
};

export default ChatSection;
