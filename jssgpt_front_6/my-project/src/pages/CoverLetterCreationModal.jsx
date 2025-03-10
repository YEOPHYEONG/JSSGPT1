// src/pages/CoverLetterCreationModal.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import styles from './CoverLetterCreationModal.module.css';
import { getCookie } from '../utils/utils';

const CoverLetterCreationModal = ({ recruitJobId, onClose, onGenerationComplete }) => {
  const [step, setStep] = useState(1); // 1: "초안 작성할까요?" / 2: 매칭 폼 / 3: 생성 중
  const [prompts, setPrompts] = useState([]);
  const [formData, setFormData] = useState({}); // { promptId: selectedStarId }
  const [allStars, setAllStars] = useState([]); // 전체 STARExperience 목록 for the user
  const [loading, setLoading] = useState(false); // Step 3: 생성 중 로딩 상태
  const [isMatchingLoading, setIsMatchingLoading] = useState(true); // Step 2: 추천 데이터 로딩 상태

  // Step 2: 추천 데이터와 전체 STARExperience 목록을 fetch
  useEffect(() => {
    if (step === 2) {
      setIsMatchingLoading(true);
      Promise.all([
        axios.get(`/api/cover-letter/create/${recruitJobId}/`, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          withCredentials: true,
        }),
        axios.get(`/api/user-experience/star-experiences/`, { withCredentials: true })
      ])
      .then(([createResponse, starsResponse]) => {
        const data = createResponse.data;
        setPrompts(data.prompts);
        const initial = {};
        data.prompts.forEach(item => {
          const promptId = item.prompt.id;
          // 추천된 경험은 단 1개만 기본값으로 사용
          if (item.recommended && item.recommended.length > 0) {
            initial[promptId] = item.recommended[0].id;
          } else {
            initial[promptId] = '';
          }
        });
        setFormData(initial);
        setAllStars(starsResponse.data);
      })
      .catch(error => {
        console.error("Failed to load matching data:", error);
      })
      .finally(() => {
        setIsMatchingLoading(false);
      });
    }
  }, [step, recruitJobId]);

  const handleConfirmation = (confirm) => {
    if (confirm) {
      setStep(2);
    } else {
      onClose();
    }
  };

  const handleFormChange = (promptId, value) => {
    setFormData(prev => ({ ...prev, [promptId]: value }));
  };

  const handleSubmit = async () => {
    const csrfToken = getCookie('csrftoken');  // CSRF 토큰 가져오기
    const formPayload = new FormData();
    Object.keys(formData).forEach(promptId => {
      formPayload.append(`selected_star_${promptId}`, formData[promptId]);
    });
    try {
      // 선택된 STAR 경험을 저장
      await axios.post(
        `/api/cover-letter/create/${recruitJobId}/`,
        formPayload,
        {
          headers: { 'X-CSRFToken': csrfToken },
          withCredentials: true,
        }
      );
      // 초안 생성 요청
      setStep(3);
      setLoading(true);
      await axios.post(
        `/api/cover-letter/generate-draft/${recruitJobId}/`,
        {},
        {
          headers: { 'X-CSRFToken': csrfToken },
          withCredentials: true,
        }
      );
      setLoading(false);
      onGenerationComplete();
    } catch (error) {
      console.error("Error during cover letter generation:", error);
      alert("자기소개서 생성 중 오류가 발생했습니다.");
      setLoading(false);
    }
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        {step === 1 && (
          <div className={styles.stepContainer}>
            <h2 className={styles.stepTitle}>자기소개서 초안을 작성할까요?</h2>
            <div className={styles.buttonGroup}>
              <button className={styles.cancelButton} onClick={() => handleConfirmation(false)}>
                아뇨..
              </button>
              <button className={styles.confirmButton} onClick={() => handleConfirmation(true)}>
                네!!
              </button>
            </div>
          </div>
        )}
        {step === 2 && (
          <div className={styles.stepContainer}>
            {isMatchingLoading ? (
              <>
                <h2 className={styles.stepTitle}>AI가 경험을 추천중이에요</h2>
                <div className={styles.loadingAnimation}></div>
              </>
            ) : (
              <>
                <h2 className={styles.stepTitle}>각 문항과 매칭시킬 경험을 선택해주세요!!</h2>
                <p className={styles.stepSubtitle}>
                  *추천된 경험은 기본 선택되어 있습니다. 드롭다운을 열어 모든 경험 중 선택할 수 있습니다.
                </p>
                {prompts.map(item => {
                  const promptId = item.prompt.id;
                  return (
                    <div key={promptId} className={styles.promptRow}>
                      <label className={styles.questionLabel}>
                        {item.prompt.question_text}
                      </label>
                      <select
                        className={styles.selectBox}
                        value={formData[promptId] || ''}
                        onChange={(e) => handleFormChange(promptId, e.target.value)}
                      >
                        {allStars.map(star => (
                          <option key={star.id} value={star.id}>
                            {star.title}
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                })}
                <div className={styles.buttonGroup}>
                  <button className={styles.submitButton} onClick={handleSubmit}>
                    생성 시작!
                  </button>
                  <button className={styles.cancelButton} onClick={onClose}>
                    취소
                  </button>
                </div>
              </>
            )}
          </div>
        )}
        {step === 3 && (
          <div className={styles.stepContainer}>
            {loading ? (
              <>
                <h2 className={styles.stepTitle}>AI가 자기소개서를 생성중입니다...</h2>
                <div className={styles.loadingAnimation}></div>
              </>
            ) : (
              <p>생성이 완료되었습니다.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CoverLetterCreationModal;
