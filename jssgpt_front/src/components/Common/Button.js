import React from 'react';
import { Button as MuiButton } from '@mui/material';

/**
 * Reusable Button Component
 * @param {string} variant - The variant of the button ('contained', 'outlined', 'text')
 * @param {string} color - The color of the button ('primary', 'secondary', etc.)
 * @param {object} props - Additional props for the MUI Button
 */
const Button = ({ children, variant = 'contained', color = 'primary', ...props }) => {
  return (
    <MuiButton variant={variant} color={color} {...props}>
      {children}
    </MuiButton>
  );
};

export default Button;
