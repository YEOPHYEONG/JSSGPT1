// src/pages/CoverLetterList.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import styles from './CoverLetterList.module.css';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';

const CoverLetterList = () => {
  const [coverLetters, setCoverLetters] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchCoverLetters();
  }, []);

  const fetchCoverLetters = async () => {
    try {
      const response = await axios.get('/api/cover-letter/list/', {
        withCredentials: true,
      });
      setCoverLetters(response.data);
    } catch (err) {
      console.error(err);
      setError('자기소개서 목록을 불러오지 못했습니다.');
    }
  };

  const handleCardClick = (letter) => {
    navigate('/essay', {
      state: {
        companyName: letter.company_name,
        recruitmentTitle: letter.recruit_job_title,
        questions: letter.essay_questions,
        recruitJobId: letter.recruit_job_id,
      },
    });
  };

  // 검색된 자기소개서만 필터링
  const filteredLetters = coverLetters.filter((letter) =>
    letter.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    letter.recruit_job_title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      <Header />
      <div className={styles.container}>
        <h1 className={styles.pageTitle}>자기소개서 관리</h1>

        {error && <p className={styles.error}>{error}</p>}

        <p className={styles.subtitle}>내가 작성한 자기소개서를 관리해보세요</p>

        <div className={styles.searchContainer}>
          <input 
            type="text" 
            className={styles.searchInput} 
            placeholder="자기소개서를 검색하세요..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button className={styles.searchButton}>검색</button>
        </div>

        <hr className={styles.separator} />

        <div className={styles.cardGrid}>
          {filteredLetters.map((letter) => (
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

              <hr className={styles.separator} />

              <div className={styles.cardBody}>
                💼 직무 <div className={styles.recruitJob}>{letter.recruit_job_title}</div>
                {letter.essay_questions &&
                  letter.essay_questions.map((q, idx) => (
                    <div key={idx} className={styles.essayQuestion}>
                      📝 {q.question_text}
                      {q.content && (
                        <div className={styles.essayPreview}>
                          {q.content.length > 100
                            ? q.content.slice(0, 100) + '...'
                            : q.content}
                        </div>
                      )}
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
