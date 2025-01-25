import React from 'react';
import { Modal as MuiModal, Box, Typography, Button } from '@mui/material';

/**
 * Reusable Modal Component
 * @param {boolean} open - If true, the modal is open
 * @param {function} onClose - Function to handle modal close
 * @param {string} title - Title of the modal
 * @param {ReactNode} children - Content of the modal
 */
const Modal = ({ open, onClose, title, children }) => {
  return (
    <MuiModal open={open} onClose={onClose}>
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 400,
          bgcolor: 'background.paper',
          border: '2px solid #000',
          boxShadow: 24,
          p: 4,
          borderRadius: 2,
        }}
      >
        <Typography variant="h6" component="h2" gutterBottom>
          {title}
        </Typography>
        <Box sx={{ mt: 2 }}>{children}</Box>
        <Box sx={{ mt: 2, textAlign: 'right' }}>
          <Button variant="contained" color="primary" onClick={onClose}>
            Close
          </Button>
        </Box>
      </Box>
    </MuiModal>
  );
};

export default Modal;
