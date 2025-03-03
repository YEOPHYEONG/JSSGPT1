// src/pages/ExperienceEdit.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import styles from './ExperienceEdit.module.css';
import { useNavigate } from 'react-router-dom';
import { getCookie } from '../utils/utils';
import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';

const ExperienceEdit = () => {
  const [starExperiences, setStarExperiences] = useState([]);
  const [error, setError] = useState('');
  const [dropdownValue, setDropdownValue] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchStarExperiences();
  }, []);

  // 백엔드에서 STARExperience 목록을 가져옴
  const fetchStarExperiences = async () => {
    try {
      const response = await axios.get(
        '/user-experience/star-experiences/',
        { withCredentials: true }
      );
      setStarExperiences(response.data);
    } catch (err) {
      console.error(err);
      setError('경험 데이터를 불러오지 못했습니다.');
    }
  };

  const handleDropdownChange = (e) => {
    setDropdownValue(e.target.value);
  };

  // 각 항목의 필드 변경 처리 (title 포함)
  const handleFieldChange = (index, field, value) => {
    const updatedExperiences = [...starExperiences];
    updatedExperiences[index] = { ...updatedExperiences[index], [field]: value };
    setStarExperiences(updatedExperiences);
  };

  // 수정한 내용을 백엔드에 저장
  const handleSave = async (id, index) => {
    try {
      const csrfToken = getCookie('csrftoken');
      const experience = starExperiences[index];
      const response = await axios.put(
        `/user-experience/star-experiences/${id}/update/`,
        {
          title: experience.title,
          situation: experience.situation,
          task: experience.task,
          action: experience.action,
          result: experience.result
        },
        {
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
          },
          withCredentials: true,
        }
      );
      if (response.data.message) {
        alert("저장되었습니다!");
        fetchStarExperiences(); // 변경사항 반영을 위해 재조회
      } else {
        alert("저장 실패하였습니다.");
      }
    } catch (err) {
      console.error(err);
      alert("서버 오류가 발생하였습니다.");
    }
  };

  // 2. 경험 추가하기: 새 STARExperience를 DB에 생성 -> 화면 최상단에 추가
  const handleAddExperience = async () => {
    try {
      const csrfToken = getCookie('csrftoken');
      const response = await axios.post(
        '/user-experience/star-experiences/create/',
        {
          title: '',
          situation: '',
          task: '',
          action: '',
          result: ''
        },
        {
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
          },
          withCredentials: true,
        }
      );
      // 서버에서 새로 생성된 객체를 반환한다고 가정
      const newExp = response.data; 
      // 새 경험을 최상단에 삽입
      setStarExperiences((prev) => [newExp, ...prev]);
    } catch (err) {
      console.error(err);
      alert("새 경험 추가 중 오류가 발생했습니다.");
    }
  };

  return (
    <>
      <Header />
      <div className={styles.container}>
        {/* 상단 헤더 부분(제목 + '경험 추가하기' 버튼) */}
        <div className={styles.headerBar}>
          <h1 className={styles.title}>경험 편집</h1>
          <button className={styles.addButton} onClick={handleAddExperience}>
            경험 추가하기
          </button>
        </div>

        {error && <p className={styles.error}>{error}</p>}

        {/* 1. 드롭다운메뉴 (현재 기능은 비워둠) */}
        <select
          className={styles.dropdown}
          value={dropdownValue}
          onChange={handleDropdownChange}
        >
          <option value="">선택</option>
          {/* 추후에 필요한 옵션이 있다면 여기에 추가 */}
        </select>

        {/* 2. 경험별 STAR구조 창 (수정 가능) */}
        {starExperiences.map((exp, index) => (
          <div key={exp.id} className={styles.starContainer}>
            {/* Title도 편집 가능 */}
            <div className={styles.starItem}>
              <label className={styles.starLabel}>제목</label>
              <input
                type="text"
                className={styles.starInput}
                value={exp.title}
                onChange={(e) => handleFieldChange(index, 'title', e.target.value)}
              />
            </div>

            <div className={styles.starItem}>
              <label className={styles.starLabel}>상황</label>
              <textarea
                className={styles.starInput}
                value={exp.situation}
                onChange={(e) => handleFieldChange(index, 'situation', e.target.value)}
              />
            </div>

            <div className={styles.starItem}>
              <label className={styles.starLabel}>과업</label>
              <textarea
                className={styles.starInput}
                value={exp.task}
                onChange={(e) => handleFieldChange(index, 'task', e.target.value)}
              />
            </div>

            <div className={styles.starItem}>
              <label className={styles.starLabel}>행동</label>
              <textarea
                className={styles.starInput}
                value={exp.action}
                onChange={(e) => handleFieldChange(index, 'action', e.target.value)}
              />
            </div>

            <div className={styles.starItem}>
              <label className={styles.starLabel}>결과</label>
              <textarea
                className={styles.starInput}
                value={exp.result}
                onChange={(e) => handleFieldChange(index, 'result', e.target.value)}
              />
            </div>

            <button
              className={styles.saveButton}
              onClick={() => handleSave(exp.id, index)}
            >
              저장
            </button>
          </div>
        ))}
      </div>
      <Footer />
    </>
  );
};

export default ExperienceEdit;
