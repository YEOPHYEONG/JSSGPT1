// src/router/AppRouter.jsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from '../pages/Home';
import CompanyRecruitDetail from '../pages/CompanyRecruitDetail';
import EssayWrite from '../pages/EssayWrite';
import Login from '../pages/Login';
import UploadResume from '../pages/UploadResume';
import ExperienceEdit from '../pages/ExperienceEdit';
import CoverLetterList from '../pages/CoverLetterList'; 

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 메인 홈(채용공고 달력) */}
        <Route path="/" element={<Home />} />

        {/* 기업 채용공고 상세 */}
        <Route path="/company/:companyName/:recruitmentId" element={<CompanyRecruitDetail />} />

        {/* 자기소개서 작성 페이지 */}
        <Route path="/essay" element={<EssayWrite />} />

        <Route path="/login" element={<Login />} />

        {/* 추가: 이력서 업로드 페이지 */}
        <Route path="/upload-resume" element={<UploadResume />} />

        {/* 경험 편집 페이지 */}
        <Route path="/experience-edit" element={<ExperienceEdit />} />

        {/* 자기소개서 관리 페이지 */}
        <Route path="/cover-letter" element={<CoverLetterList />} />

      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;
