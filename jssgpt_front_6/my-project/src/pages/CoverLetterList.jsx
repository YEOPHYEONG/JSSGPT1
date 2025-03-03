// src/pages/CoverLetterList.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import styles from './CoverLetterList.module.css';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';

const CoverLetterList = () => {
  const [coverLetters, setCoverLetters] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchCoverLetters();
  }, []);

  const fetchCoverLetters = async () => {
    try {
        const response = await axios.get(
            '/cover-letter/list/',
            { withCredentials: true }
        );
      setCoverLetters(response.data);
    } catch (err) {
      console.error(err);
      setError('자기소개서 목록을 불러오지 못했습니다.');
    }
  };

  // 카드 클릭 시 EssayWrite 페이지로 이동하며, 필요한 state 전달
  const handleCardClick = (letter) => {
    navigate('/essay', {
      state: {
        companyName: letter.company_name,
        recruitmentTitle: letter.recruit_job_title,
        questions: letter.essay_questions,  // 각 문항은 { id, question_text, limit } 형태
        recruitJobId: letter.recruit_job_id,
      },
    });
  };

  return (
    <>
      <Header />
      <div className={styles.container}>
        <h1 className={styles.pageTitle}>자기소개서 관리</h1>
        {error && <p className={styles.error}>{error}</p>}
        <div className={styles.cardGrid}>
          {coverLetters.map((letter) => (
            <div
              key={letter.id}
              className={styles.card}
              onClick={() => handleCardClick(letter)}
            >
              <div className={styles.cardHeader}>
                <div className={styles.companyName}>{letter.company_name}</div>
                <div className={styles.updatedAt}>
                  {new Date(letter.updated_at).toLocaleString()}
                </div>
              </div>
              <div className={styles.cardBody}>
                <div className={styles.recruitJob}>{letter.recruit_job_title}</div>
                {letter.essay_questions &&
                  letter.essay_questions.map((q, idx) => (
                    <div key={idx} className={styles.essayQuestion}>
                      {q.question_text}
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      <Footer />
    </>
  );
};

export default CoverLetterList;
