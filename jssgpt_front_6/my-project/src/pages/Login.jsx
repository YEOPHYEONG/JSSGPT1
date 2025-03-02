// src/pages/Login.jsx
import React from 'react';
import GoogleLoginButton from '../components/GoogleLoginButton';
import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';
import styles from './Login.module.css';

const Login = () => {
  return (
    <div className={styles.loginPage}>
      <Header />
      <div className={styles.loginContainer}>
        <div className={styles.loginBox}>
          <GoogleLoginButton />
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Login;
