import React from 'react';
import { Box, Typography } from '@mui/material';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';

const CalendarComponent = () => {
  return (
    <Box sx={{ p: 2, borderRight: '1px solid #ddd', height: '100%' }}>
      <Typography variant="h6" gutterBottom>
        달력
      </Typography>
      <Calendar />
    </Box>
  );
};

export default CalendarComponent;
