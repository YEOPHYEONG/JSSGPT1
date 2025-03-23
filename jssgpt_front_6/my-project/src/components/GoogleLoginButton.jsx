// src/components/GoogleLoginButton.jsx
import React, { useContext } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';
import { AuthContext } from '../contexts/AuthContext';

const GoogleLoginButton = () => {
  const { login } = useContext(AuthContext);

  const handleLoginSuccess = async (credentialResponse) => {
    try {
      const idToken = credentialResponse.credential;
      const res = await axios.post('/api/auth/google/callback/', {
        access_token: idToken,
      }, { withCredentials: true });
      
      console.log("Login response data:", res.data);
      const { user } = res.data;
      login(user);
      
      alert(`로그인 성공! ${user.username}님 환영합니다.`);
      window.location.href = '/';
    } catch (error) {
      console.error('소셜 로그인 실패:', error);
      alert('로그인에 실패했습니다.');
    }
  };

  const handleLoginError = () => {
    alert('Google 로그인 실패!');
  };

  return (
    <div className="google-login-container">
      <GoogleLogin 
        theme="filled_black"
        size="large"
        text="signin_with"
        shape="rectangular"
        width="250px"
        onSuccess={handleLoginSuccess}
        onError={handleLoginError}
      />
    </div>
  );
};

export default GoogleLoginButton;
