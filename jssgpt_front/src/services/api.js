import axios from 'axios';

// Axios instance
const api = axios.create({
  baseURL: '/api', // API 엔드포인트의 기본 URL
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // 요청 전에 공통적으로 처리해야 할 작업 (예: 인증 토큰 추가)
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 응답 에러 처리 (예: 인증 실패, 네트워크 에러 등)
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;
