// GoogleLoginButton.jsx
import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';

const GoogleLoginButton = () => {
  const handleLoginSuccess = async (response) => {
    try {
      // Google에서 받은 id_token (response.credential)
      const idToken = response.credential;

      // 백엔드로 id_token 전달
      const res = await axios.post('http://127.0.0.1:8000/auth/google/callback/', {
        access_token: idToken, // 백엔드에서는 이를 id_token으로 처리합니다.
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
