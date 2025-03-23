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
  const [deletedExperiences, setDeletedExperiences] = useState([]);
  const [error, setError] = useState('');
  const [dropdownValue, setDropdownValue] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchStarExperiences();
  }, []);

  const fetchStarExperiences = async () => {
    try {
      const response = await axios.get(
        '/api/user-experience/star-experiences/',
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

  const handleFieldChange = (index, field, value) => {
    const updated = [...starExperiences];
    updated[index] = { ...updated[index], [field]: value };
    setStarExperiences(updated);
  };

  const handleSave = async (id, index) => {
    try {
      const csrfToken = getCookie('csrftoken');
      const exp = starExperiences[index];
      const response = await axios.put(
        `/api/user-experience/star-experiences/${id}/update/`,
        {
          title: exp.title,
          situation: exp.situation,
          task: exp.task,
          action: exp.action,
          result: exp.result
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
        fetchStarExperiences();
      } else {
        alert("저장 실패하였습니다.");
      }
    } catch (err) {
      console.error(err);
      alert("서버 오류가 발생하였습니다.");
    }
  };

  const handleAddExperience = async () => {
    try {
      const csrfToken = getCookie('csrftoken');
      const response = await axios.post(
        '/api/user-experience/star-experiences/create/',
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
      const newExp = response.data;
      setStarExperiences((prev) => [newExp, ...prev]);
    } catch (err) {
      console.error(err);
      alert("새 경험 추가 중 오류가 발생했습니다.");
    }
  };

  const handleDeleteExperience = (index) => {
    if (window.confirm("이 경험을 삭제하시겠습니까?")) {
      const deleted = starExperiences[index];
      setDeletedExperiences([...deletedExperiences, deleted]);
      setStarExperiences(starExperiences.filter((_, i) => i !== index));
    }
  };

  const handleRestoreExperience = (index) => {
    const restored = deletedExperiences[index];
    setStarExperiences([...starExperiences, restored]);
    setDeletedExperiences(deletedExperiences.filter((_, i) => i !== index));
  };

  return (
    <>
      <Header />
      <div className={styles.container}>
        <div className={styles.headerBar}>
          <h1 className={styles.title}>경험 편집</h1>
          <button className={styles.addButton} onClick={handleAddExperience}>
            ➕ 경험 추가하기
          </button>
        </div>

        <p className={styles.subtitle}>
          내 경험, 내가 다듬는다! ✍️ 경험을 수정하고 자소서를 완성해봐요!💫💯
        </p>

        <hr className={styles.separator} />

        {error && <p className={styles.error}>{error}</p>}

        <select
          className={styles.dropdown}
          value={dropdownValue}
          onChange={handleDropdownChange}
        >
          <option value="">필요한옵션기능추가예정</option>
        </select>

        {starExperiences.map((exp, index) => (
          <div key={exp.id} className={styles.starContainer}>
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
              <label className={styles.starLabel}>상황(Situation)</label>
              <textarea
                className={styles.starInput}
                value={exp.situation}
                onChange={(e) => handleFieldChange(index, 'situation', e.target.value)}
              />
            </div>

            <div className={styles.starItem}>
              <label className={styles.starLabel}>과업(Task)</label>
              <textarea
                className={styles.starInput}
                value={exp.task}
                onChange={(e) => handleFieldChange(index, 'task', e.target.value)}
              />
            </div>

            <div className={styles.starItem}>
              <label className={styles.starLabel}>행동(Action)</label>
              <textarea
                className={styles.starInput}
                value={exp.action}
                onChange={(e) => handleFieldChange(index, 'action', e.target.value)}
              />
            </div>

            <div className={styles.starItem}>
              <label className={styles.starLabel}>결과(Result)</label>
              <textarea
                className={styles.starInput}
                value={exp.result}
                onChange={(e) => handleFieldChange(index, 'result', e.target.value)}
              />
            </div>

            <div className={styles.buttonContainer}>
              <button
                className={styles.saveButton}
                onClick={() => handleSave(exp.id, index)}
              >
                💾저장
              </button>
              <button
                className={styles.deleteButton}
                onClick={() => handleDeleteExperience(index)}
              >
                🗑️제거
              </button>
            </div>
          </div>
        ))}

        {deletedExperiences.length > 0 && (
          <div className={styles.restoreContainer}>
            <h3>삭제된 경험</h3>
            {deletedExperiences.map((exp, index) => (
              <div key={index} className={styles.deletedExperience}>
                <span>{exp.title}</span>
                <button
                  className={styles.restoreButton}
                  onClick={() => handleRestoreExperience(index)}
                >
                  복원
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      <Footer />
    </>
  );
};

export default ExperienceEdit;
