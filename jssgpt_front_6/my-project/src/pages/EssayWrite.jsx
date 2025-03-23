import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import classNames from 'classnames';
import axios from 'axios';
import styles from './EssayWrite.module.css';
import { getCookie } from '../utils/utils';

import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';

// 자동 저장 API 함수
async function saveEssayToDB(companyName, recruitmentTitle, promptId, recruitJobId, content) {
  const csrfToken = getCookie('csrftoken');
  console.log('[AutoSave] 시도:', { promptId, recruitJobId, content, csrfToken });

  return axios.put(
    '/api/cover-letter/update-content/',
    {
      prompt_id: promptId,
      recruit_job_id: recruitJobId,
      content,
    },
    {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
    }
  );
}

function EssayWrite() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const recruitJobIdFromQuery = searchParams.get("recruitJobId");

  // 최초 state에서 받아오려 시도
  const {
    companyName: initialCompanyName,
    recruitmentTitle: initialRecruitmentTitle,
    questions: initialQuestions,
    recruitJobId: initialRecruitJobId,
  } = location.state || {};

  const [companyName, setCompanyName] = useState(initialCompanyName);
  const [recruitmentTitle, setRecruitmentTitle] = useState(initialRecruitmentTitle);
  const [recruitJobId, setRecruitJobId] = useState(initialRecruitJobId || recruitJobIdFromQuery);
  const [questions, setQuestions] = useState(initialQuestions || []);
  const [coverContentMap, setCoverContentMap] = useState({});
  const [essayContents, setEssayContents] = useState([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPolling, setIsPolling] = useState(true);
  const [typingTimer, setTypingTimer] = useState(null);
  const [lastSavedContent, setLastSavedContent] = useState('');
  const [isComposing, setIsComposing] = useState(false);

  // ✅ fallback: location.state 없을 경우 백엔드 fetch
  useEffect(() => {
    if ((!initialCompanyName || !initialRecruitmentTitle || !initialQuestions) && recruitJobId) {
      axios.get(`/api/cover-letter/get/?recruit_job_id=${recruitJobId}`, {
        withCredentials: true,
      })
      .then(res => {
        const data = res.data;
        const hasContent = Object.values(data).some(content => content && content.trim().length > 0);
        if (hasContent) {
          setCoverContentMap(data);
          // 여기서 필요한 질문 정보도 임의 생성 (question_text는 알 수 없으므로 placeholder 사용)
          const formattedQuestions = Object.keys(data).map((id, idx) => ({
            id: parseInt(id),
            question_text: `질문 ${idx + 1}`,
            content: data[id],
            limit: 1000,
          }));
          setQuestions(formattedQuestions);
        }
        setIsPolling(false);
      })
      .catch(err => {
        console.error("Fallback fetch failed:", err);
      });
    }
  }, [initialCompanyName, initialRecruitmentTitle, initialQuestions, recruitJobId]);

  // 폴링
  useEffect(() => {
    const interval = setInterval(() => {
      axios.get(`/api/cover-letter/get/?recruit_job_id=${recruitJobId}`, {
        withCredentials: true,
      })
      .then(res => {
        const data = res.data;
        const hasContent = Object.values(data).some(content => content && content.trim().length > 0);
        if (hasContent) {
          setCoverContentMap(data);
          setIsPolling(false);
          clearInterval(interval);
        }
      })
      .catch(err => {
        console.error("Polling cover letter content failed:", err);
      });
    }, 3000);
    return () => clearInterval(interval);
  }, [recruitJobId]);

  const mergedQuestions = useMemo(() => {
    return questions.map(q => ({
      ...q,
      content: coverContentMap[q.id] !== undefined ? coverContentMap[q.id] : (q.content || '')
    }));
  }, [questions, coverContentMap]);

  useEffect(() => {
    if (Object.keys(coverContentMap).length > 0) {
      const newContents = mergedQuestions.map(q => coverContentMap[q.id] || q.content || '');
      setEssayContents(newContents);
      if (newContents[activeIndex] !== undefined) {
        setLastSavedContent(newContents[activeIndex]);
      }
    }
  }, [coverContentMap, activeIndex, mergedQuestions]);

  const currentContent = essayContents[activeIndex] || '';
  const currentLimit = mergedQuestions[activeIndex]?.limit || 1000;
  const currentQuestionText = mergedQuestions[activeIndex]?.question_text || '';

  const handleAutoSave = useCallback(async () => {
    if (currentContent.trim().length === 0) return;
    if (currentContent === lastSavedContent) return;
    try {
      const promptId = mergedQuestions[activeIndex].id;
      await saveEssayToDB(companyName, recruitmentTitle, promptId, recruitJobId, currentContent);
      setLastSavedContent(currentContent);
    } catch (error) {
      console.error("Auto-save failed:", error);
    }
  }, [companyName, recruitmentTitle, activeIndex, currentContent, mergedQuestions, recruitJobId, lastSavedContent]);

  const handleChange = (e) => {
    const newContent = e.target.value;
    setEssayContents(prev => {
      const newArr = [...prev];
      newArr[activeIndex] = newContent;
      return newArr;
    });
    if (isComposing) return;
    if (typingTimer) clearTimeout(typingTimer);
    const newTimer = setTimeout(() => {
      handleAutoSave();
    }, 3000);
    setTypingTimer(newTimer);
  };

  const handleCompositionStart = () => setIsComposing(true);
  const handleCompositionEnd = (e) => {
    setIsComposing(false);
    handleChange(e);
  };

  const handleTabClick = (index) => {
    handleAutoSave();
    setActiveIndex(index);
  };

  useEffect(() => {
    return () => {
      if (typingTimer) clearTimeout(typingTimer);
      handleAutoSave();
    };
  }, [typingTimer, handleAutoSave]);

  const handleGoBack = () => {
    handleAutoSave();
    navigate(-1);
  };

  return (
    <>
      <Header />
      {isPolling ? (
        <div className={styles.loadingContainer}>
          <div className={styles.loadingContent}>
            <div className={styles.spinner}></div>
            <p className={styles.loadingText}>자기소개서를 불러오는 중입니다...</p>
            <button className={styles.backButton} onClick={handleGoBack}>
              뒤로가기
            </button>
          </div>
        </div>
      ) : (
        <div className={styles.essayContainer}>
          <div className={styles.leftSection}>
            <div className={styles.topBar}>
              <span className={styles.companyName}>{companyName || '회사명 없음'}</span>
              <span className={styles.recruitmentTitle}> 💼 채용직무 : {recruitmentTitle || '직무명 없음'}</span>
            </div>
            <div className={styles.essayWriteArea}>
              <div className={styles.questionTabs}>
                {mergedQuestions.map((q, index) => (
                  <div
                    key={q.id}
                    className={classNames(styles.tabItem, {
                      [styles.activeTab]: activeIndex === index,
                    })}
                    onClick={() => handleTabClick(index)}
                  >
                    {index + 1}번
                  </div>
                ))}
              </div>
              <div className={styles.essayBox}>
                <div className={styles.questionText}>📝 {currentQuestionText}</div>
                <div className={styles.charCount}>
                  {currentContent.length} / {currentLimit}
                </div>
                <hr className={styles.separator} />
                <textarea
                  className={styles.textArea}
                  value={currentContent}
                  onChange={handleChange}
                  onCompositionStart={handleCompositionStart}
                  onCompositionEnd={handleCompositionEnd}
                  placeholder="여기에 작성하세요..."
                />
              </div>
            </div>
          </div>
          <div className={styles.rightSection}>
            <p className={styles.aiNotice}>
              실시간으로 대화하며 작성할 수 있는 AI 도우미가 들어올 예정입니다.
            </p>
          </div>
        </div>
      )}
      <div className={styles.bottomBar}>
        <button className={styles.backButton} onClick={handleGoBack}>
          뒤로가기
        </button>
      </div>
      <Footer />
    </>
  );
}

export default EssayWrite;
