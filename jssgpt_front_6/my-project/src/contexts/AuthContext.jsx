// src/contexts/AuthContext.jsx
import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  // 앱 시작 시 현재 로그인한 사용자 정보를 복원하는 API 호출 (예시)
  useEffect(() => {
    async function fetchCurrentUser() {
      try {
        const res = await axios.get('http://127.0.0.1:8000/auth/current-user/', { withCredentials: true });
        setUser(res.data);
      } catch (error) {
        console.error("Failed to fetch current user:", error);
        setUser(null);
      }
    }
    fetchCurrentUser();
  }, []);

  const login = (userData) => {
    setUser(userData);
  };

  const logout = () => {
    // 세션 기반이므로 로컬 스토리지는 사용하지 않음.
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;
