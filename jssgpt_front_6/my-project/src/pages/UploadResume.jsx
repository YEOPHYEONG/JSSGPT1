// src/pages/UploadResume.jsx
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import styles from './UploadResume.module.css';
import { getCookie } from '../utils/utils';
import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';

const UploadResume = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
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

    setUploading(true);

    try {
      const csrfToken = getCookie('csrftoken');
      const response = await axios.post(
        '/api/user-experience/upload-resume/', // ✅ 변경된 API 경로
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'X-CSRFToken': csrfToken,
          },
          withCredentials: true,
        }
      );

      if (response.data.message) {
        setSuccessMessage('이력서 업로드가 완료되었습니다!');
        setTimeout(() => navigate('/experience-edit'), 2000); // ✅ 성공 후 이동 처리
      } else {
        setError('업로드에 실패하였습니다. 다시 시도해주세요.');
      }
    } catch (err) {
      console.error(err);
      setError('서버 오류가 발생하였습니다.');
    } finally {
      setUploading(false); // ✅ 로딩 상태 해제
    }
  };

  return (
    <>
      <Header />
      <div className={styles.container}>
        <form onSubmit={handleUpload} className={styles.form}>
          <label htmlFor="resume-upload" className={styles.uploadLabel}>
            📤 이력서 업로드
          </label>
          <input
            id="resume-upload"
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className={styles.fileInput}
          />

          <h1 className={styles.title}>📁 업로드된 이력서</h1>
          <p className={styles.subtitle}>"이력서 업로드 이용방법"</p>
          <p className={styles.subtitle}>1. 분석하고 싶은 이력서를 먼저 업로드해보세요 (오른쪽 상단)</p>
          <p className={styles.subtitle}>2. 업로드된 이력서를 확인하고 이력서 분석을 실행해보세요 (노란버튼)</p>

          {error && <p className={styles.error}>{error}</p>}
          {uploading && <p className={styles.uploading}>업로드 중...</p>}
          {successMessage && <p className={styles.success}>{successMessage}</p>}
          {selectedFile && (
            <p className={styles.fileName}>
              📌선택된 파일: <span className={styles.underline}>{selectedFile.name}</span>
            </p>
          )}

          <button type="submit" className={styles.uploadButton} disabled={uploading}>
            {uploading ? '업로드 중...' : '이력서 분석 START!'}
          </button>
        </form>
      </div>
      <Footer />
    </>
  );
};

export default UploadResume;
