// src/pages/EssayWrite.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import classNames from 'classnames';
import axios from 'axios';
import styles from './EssayWrite.module.css';
import { getCookie } from '../utils/utils';

import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';

// 자동 저장 API 함수: DB의 cover letter content 업데이트
async function saveEssayToDB(companyName, recruitmentTitle, promptId, recruitJobId, content) {
  console.log(
    `[AutoSave] company=${companyName}, recruitment=${recruitmentTitle}, promptId=${promptId}, content=${content}`
  );
  const csrfToken = getCookie('csrftoken');
  return axios.put(
    `/cover-letter/update-content/`,
    {
      prompt_id: promptId,
      recruit_job_id: recruitJobId,
      content: content,
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
  const { companyName, recruitmentTitle, questions, recruitJobId } = location.state || {};

  // 필수 데이터가 없으면 5초 후에 페이지 새로고침
  useEffect(() => {
    if (!companyName || !recruitmentTitle || !questions || !recruitJobId) {
      const timer = setTimeout(() => {
        window.location.reload();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [companyName, recruitmentTitle, questions, recruitJobId]);

  if (!companyName || !recruitmentTitle || !questions || !recruitJobId) {
    return <p>필수 정보가 부족합니다. 5초 후에 다시 시도합니다...</p>;
  }

  // 현재 선택된 질문(탭) 인덱스
  const [activeIndex, setActiveIndex] = useState(0);
  const initialContents = questions.map(q => q.content || '');
  const [essayContents, setEssayContents] = useState(initialContents);
  // DB에서 가져온 cover letter 내용: { promptId: content }
  const [coverContentMap, setCoverContentMap] = useState({});
  const [isPolling, setIsPolling] = useState(true);
  const [typingTimer, setTypingTimer] = useState(null);
  // 마지막 저장된 내용 추적
  const [lastSavedContent, setLastSavedContent] = useState('');
  // IME 조합 상태 추적
  const [isComposing, setIsComposing] = useState(false);

  // 폴링: 일정 간격마다 DB에서 cover letter 내용을 가져옴
  useEffect(() => {
    const interval = setInterval(() => {
      axios.get(`/cover-letter/get/?recruit_job_id=${recruitJobId}`, {
        withCredentials: true,
      })
      .then(res => {
        const data = res.data; // 예: { "1": "내용...", "3": "내용...", ... }
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

  // mergedQuestions: questions 배열과 coverContentMap을 결합
  const mergedQuestions = useMemo(() => {
    return questions.map(q => ({
      ...q,
      content: coverContentMap[q.id] !== undefined ? coverContentMap[q.id] : (q.content || '')
    }));
  }, [questions, coverContentMap]);

  // coverContentMap 업데이트 후 essayContents 및 lastSavedContent 업데이트
  useEffect(() => {
    if (Object.keys(coverContentMap).length > 0) {
      const newContents = mergedQuestions.map(q => coverContentMap[q.id] || q.content || '');
      setEssayContents(newContents);
      if (newContents[activeIndex] !== undefined) {
        setLastSavedContent(newContents[activeIndex]);
      }
    }
  }, [coverContentMap, activeIndex, mergedQuestions]);

  const currentContent = essayContents[activeIndex];
  const currentLimit = mergedQuestions[activeIndex].limit;
  const currentQuestionText = mergedQuestions[activeIndex].question_text;

  // 자동 저장 함수: 변경된 경우에만 저장
  const handleAutoSave = useCallback(async () => {
    if (currentContent.trim().length === 0) return;
    if (currentContent === lastSavedContent) return;
    try {
      const promptId = mergedQuestions[activeIndex].id;
      await saveEssayToDB(companyName, recruitmentTitle, promptId, recruitJobId, currentContent);
      console.log("Auto-save successful");
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

  const handleCompositionStart = () => {
    setIsComposing(true);
  };

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
          <p>자기소개서 내용을 불러오는 중입니다...</p>
        </div>
      ) : (
        <div className={styles.essayContainer}>
          <div className={styles.leftSection}>
            <div className={styles.topBar}>
              <span className={styles.companyName}>{companyName}</span>
              <span className={styles.recruitmentTitle}>{recruitmentTitle}</span>
            </div>
            <div className={styles.essayWriteArea}>
              {/* 문항 탭 (가로 배치) */}
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
                <div className={styles.questionText}>{currentQuestionText}</div>
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
