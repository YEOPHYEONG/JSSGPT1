// src/pages/UploadResume.jsx
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';
import styles from './UploadResume.module.css';
import { getCookie } from '../utils/utils';  // CSRF 토큰을 가져오기 위한 유틸 함수

const UploadResume = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // 파일 선택 시 PDF 파일만 허용
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type !== 'application/pdf') {
      setError('PDF 파일만 업로드 가능합니다.');
      setSelectedFile(null);
      return;
    }
    setError('');
    setSelectedFile(file);
  };

  // 업로드 버튼 클릭 시 파일을 백엔드 업로드 API로 전송
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('파일을 선택해주세요.');
      return;
    }
    const formData = new FormData();
    formData.append('resume_file', selectedFile);

    try {
      // CSRF 토큰을 가져와서 헤더에 포함시킵니다.
      const csrfToken = getCookie('csrftoken');
      const response = await axios.post(
        '/api/user-experience/upload-resume/',
        formData,
        {
          headers: { 
            'Content-Type': 'multipart/form-data',
            'X-CSRFToken': csrfToken,
          },
          withCredentials: true,
        }
      );

      // 백엔드에서 성공 메시지가 반환되면 경험 편집 페이지로 이동
      if (response.data.message) {
        navigate('/experience-edit');
      } else {
        setError('업로드에 실패하였습니다. 다시 시도해주세요.');
      }
    } catch (err) {
      console.error(err);
      setError('서버 오류가 발생하였습니다.');
    }
  };

  return (
    <>
      {/* 상단 헤더 추가 */}
      <Header />

      <div className={styles.container}>
        <h1 className={styles.title}>이력서 업로드</h1>
        {error && <p className={styles.error}>{error}</p>}
        <form onSubmit={handleUpload} className={styles.form}>
          <label htmlFor="resume-upload" className={styles.uploadLabel}>
            이력서 업로드
          </label>
          <input
            id="resume-upload"
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className={styles.fileInput}
          />
          {/* 파일 선택 시 파일명을 표시 */}
          {selectedFile && (
            <p className={styles.fileName}>선택된 파일: {selectedFile.name}</p>
          )}
          <button type="submit" className={styles.uploadButton}>
            업로드
          </button>
        </form>
      </div>

      {/* 하단 푸터 추가 */}
      <Footer />
    </>
  );
};

export default UploadResume;
