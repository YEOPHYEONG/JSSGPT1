// src/components/Footer/Footer.jsx
import React from 'react';
import styles from './Footer.module.css';

function Footer() {
  return (
    <footer className={styles.footer}>
      <p>
      <span className={styles.sparkle}>📭 피드백 대환영! 문의 및 불편사항: geuloing@gmail.com </span> <br />
      © 2025 JSSGPT. All rights reserved. 
      </p>
    </footer>
  );
}

export default Footer;
