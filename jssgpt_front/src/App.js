import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme'; // 프로젝트에서 정의한 테마 파일
import Header from './components/Navigation/Header';
import Footer from './components/Navigation/Footer';
import Home from './pages/Home';
import Resume from './pages/Resume';
import StarExperience from './pages/StarExperience';
import CoverLetter from './pages/CoverLetter';
import CoverLetterPage from './pages/CoverLetterPage';
import SignIn from './pages/SignIn'; // 추가한 SignIn 페이지
import SignUp from './pages/SignUp'; // 추가한 회원가입 페이지
import NotFound from './pages/NotFound';
import ChatSection from './components/ChatSection';
import { GoogleOAuthProvider } from '@react-oauth/google';
import LoginPage from './pages/LoginPage'; // Google 로그인 페이지

const App = () => {
  return (
    <GoogleOAuthProvider clientId="491832134791-3enn5rutlrh7bgnk0l8dmjj9e6s30eo6.apps.googleusercontent.com"> {/* GoogleOAuthProvider 추가 */}
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Header />
          <main style={{ paddingBottom: '100px' }}> {/* 채팅 섹션과 겹치지 않도록 여백 추가 */}
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/resume" element={<Resume />} />
              <Route path="/star-experience" element={<StarExperience />} />
              <Route path="/cover-letter" element={<CoverLetter />} />
              <Route path="/cover-letter/:recruitJobId" element={<CoverLetterPage />} />
              <Route path="/signin" element={<SignIn />} /> {/* SignIn 라우트 추가 */}
              <Route path="/signup" element={<SignUp />} /> {/* 회원가입 라우트 추가 */}
              <Route path="/login" element={<LoginPage />} /> {/* Google 로그인 라우트 추가 */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          <Footer />
          <ChatSection /> {/* 추가한 채팅 섹션 */}
        </Router>
      </ThemeProvider>
    </GoogleOAuthProvider>
  );
};

export default App;
