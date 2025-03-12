// UploadResume.jsx
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';
import styles from './UploadResume.module.css';
import { getCookie } from '../utils/utils';

const UploadResume = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false); // 로딩 상태 추가
  const navigate = useNavigate();

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

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('파일을 선택해주세요.');
      return;
    }
    const formData = new FormData();
    formData.append('resume_file', selectedFile);

    setLoading(true); // 업로드 시작 전 로딩 상태 설정

    try {
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
      setLoading(false); // 업로드 성공 후 로딩 상태 해제

      if (response.data.message) {
        navigate('/experience-edit');
      } else {
        setError('업로드에 실패하였습니다. 다시 시도해주세요.');
      }
    } catch (err) {
      setLoading(false); // 오류 발생 시에도 로딩 상태 해제
      console.error(err);
      setError('서버 오류가 발생하였습니다.');
    }
  };

  // 로딩 상태일 경우 로딩창을 렌더링
  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.loadingContent}>
          <div className={styles.spinner}></div>
          <p className={styles.loadingText}>AI가 이력서를 STAR구조로 변환 중입니다...</p>
        </div>
      </div>
    );
  }

  return (
    <>
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
          {selectedFile && (
            <p className={styles.fileName}>선택된 파일: {selectedFile.name}</p>
          )}
          <button type="submit" className={styles.uploadButton}>
            업로드
          </button>
        </form>
      </div>
      <Footer />
    </>
  );
};

export default UploadResume;
