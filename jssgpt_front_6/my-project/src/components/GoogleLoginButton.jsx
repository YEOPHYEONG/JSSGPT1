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
      const res = await axios.post('http://127.0.0.1:8000/auth/google/callback/', {
        access_token: idToken,
      }, { withCredentials: true });
      
      console.log("Login response data:", res.data);
      const { user } = res.data;
      
      // 세션 기반이므로 토큰 저장은 생략 (백엔드가 세션 쿠키를 발행)
      // 로그인 성공 시 user 객체를 전역 상태에 업데이트합니다.
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
    <div>
      <GoogleLogin onSuccess={handleLoginSuccess} onError={handleLoginError} />
    </div>
  );
};

export default GoogleLoginButton;
