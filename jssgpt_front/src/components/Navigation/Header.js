import React from 'react';
import { AppBar, Toolbar, Typography, Button } from '@mui/material';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <AppBar position="static" color="primary">
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
            채용공고 관리
          </Link>
        </Typography>
        <Button color="inherit" component={Link} to="/resume">
          이력서 관리
        </Button>
        <Button color="inherit" component={Link} to="/cover-letter">
          자기소개서 작성
        </Button>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
