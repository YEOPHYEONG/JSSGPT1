import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';

const GoogleLoginButton = () => {
  const handleLoginSuccess = async (response) => {
    try {
      // Google에서 받은 Access Token
      const accessToken = response.credential;

      // 백엔드로 Access Token 전달
      const res = await axios.post('http://127.0.0.1:8000/auth/google/callback/', {
        access_token: accessToken,
      });

      const { access, refresh, user } = res.data;

      // JWT 토큰을 로컬 스토리지에 저장
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      alert(`로그인 성공! ${user.username}님 환영합니다.`);
    } catch (error) {
      console.error('소셜 로그인 실패:', error);
      alert('로그인에 실패했습니다.');
    }
  };

  const handleLoginError = () => {
    alert('Google 로그인 실패!');
  };

  return (
    <div>
      <GoogleLogin onSuccess={handleLoginSuccess} onError={handleLoginError} />
    </div>
  );
};

export default GoogleLoginButton;
