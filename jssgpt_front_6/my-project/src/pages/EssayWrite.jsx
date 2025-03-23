import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import classNames from 'classnames';
import axios from 'axios';
import styles from './EssayWrite.module.css';
import { getCookie } from '../utils/utils';

import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';

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
  const [lastSavedContent, setLastSavedContent] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const typingTimerRef = useRef(null);

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
    if (!hasInitialized && Object.keys(coverContentMap).length > 0) {
      const newContents = mergedQuestions.map(q => coverContentMap[q.id] || q.content || '');
      setEssayContents(newContents);
      setLastSavedContent(newContents[activeIndex]);
      setHasInitialized(true);
    }
  }, [coverContentMap, mergedQuestions, activeIndex, hasInitialized]);

  const currentContent = essayContents[activeIndex] || '';
  const currentLimit = mergedQuestions[activeIndex]?.limit || 1000;
  const currentQuestionText = mergedQuestions[activeIndex]?.question_text || '';

  const handleAutoSave = useCallback(async () => {
    const promptId = mergedQuestions[activeIndex]?.id;
    const content = essayContents[activeIndex];
    if (
      isSaving ||
      isComposing ||
      !promptId ||
      !content ||
      content.trim().length === 0 ||
      content === lastSavedContent
    ) return;

    try {
      setIsSaving(true);
      await saveEssayToDB(companyName, recruitmentTitle, promptId, recruitJobId, content);
      setLastSavedContent(content);

      setCoverContentMap(prev => ({
        ...prev,
        [promptId]: content,
      }));

      setEssayContents(prev => {
        const updated = [...prev];
        updated[activeIndex] = content;
        return updated;
      });

      console.log("✅ Auto-save success:", promptId);
    } catch (error) {
      console.error("❌ Auto-save failed:", error);
    } finally {
      setIsSaving(false);
    }
  }, [activeIndex, essayContents, lastSavedContent, recruitJobId, companyName, recruitmentTitle, mergedQuestions, isSaving, isComposing]);

  const handleChange = (e) => {
    const newContent = e.target.value;
    setEssayContents(prev => {
      const newArr = [...prev];
      newArr[activeIndex] = newContent;
      return newArr;
    });

    if (isComposing) return;
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);

    typingTimerRef.current = setTimeout(() => {
      handleAutoSave();
    }, 5000); // 타이핑 멈추고 5초 후에만 저장 시도
  };

  const handleCompositionStart = () => setIsComposing(true);
  const handleCompositionEnd = (e) => {
    setIsComposing(false);
    handleChange(e);
  };

  const handleTabClick = (index) => {
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    handleAutoSave();
    setLastSavedContent(essayContents[index]);
    setActiveIndex(index);
  };

  useEffect(() => {
    return () => {
      if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
      handleAutoSave();
    };
  }, [handleAutoSave]);

  const handleGoBack = () => {
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
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
