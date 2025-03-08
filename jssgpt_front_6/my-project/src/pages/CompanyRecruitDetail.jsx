// src/pages/CompanyRecruitDetail.jsx
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styles from './CompanyRecruitDetail.module.css';
import Header from '../components/Header/Header';
import Footer from '../components/Footer/Footer';
import axios from 'axios';
import CoverLetterCreationModal from './CoverLetterCreationModal';

function CompanyRecruitDetail() {
  const { companyName, recruitmentId } = useParams();
  const navigate = useNavigate();
  const [recruitData, setRecruitData] = useState(null);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);

  useEffect(() => {
    async function fetchDetail() {
      try {
        const response = await axios.get(`/api/recruitments/${recruitmentId}/`);
        console.log("Recruitment Detail:", response.data);
        setRecruitData(response.data);
      } catch (err) {
        console.error("Failed to fetch recruitment detail:", err);
        setError(err);
      }
    }
    fetchDetail();
  }, [recruitmentId]);

  const handleCardClick = async (job) => {
    try {
      const response = await axios.get(
        `/cover-letter/get/?recruit_job_id=${job.id}`,
        { withCredentials: true }
      );      
      const coverData = response.data;
      if (Object.keys(coverData).length === 0) {
        // 해당 recruit job의 cover letter가 없으면 모달 표시 (생성 프로세스 진행)
        setSelectedJob(job);
        setShowModal(true);
      } else {
        // 이미 생성되어 있다면 EssayWrite 페이지로 이동
        navigate('/essay', {
          state: {
            companyName: recruitData.company_name,
            recruitmentTitle: job.title,
            questions: job.essays, // 각 문항 객체에 id가 포함되어 있어야 합니다.
            recruitJobId: job.id,  // recruitJobId 추가
          },
        });
      }
    } catch (error) {
      console.error("Error checking cover letter existence:", error);
    }
  };
  
  const handleModalClose = () => {
    setShowModal(false);
  };

  const handleGenerationComplete = () => {
    setShowModal(false);
    // 생성 후 EssayWrite 페이지로 이동
    navigate('/essay', {
      state: {
        companyName: recruitData.company_name,
        recruitmentTitle: selectedJob.title,
        questions: selectedJob.essays,
      },
    });
  };

  if (error) return <div>Error: {error.message}</div>;
  if (!recruitData) {
    return (
      <>
        <Header />
        <div className={styles.loadingContainer}>
          <p>Loading...</p>
        </div>
        <Footer />
      </>
    );
  }

  const { company_name, start_date, end_date, recruitment_title, recruitments } = recruitData;

  return (
    <>
      <Header />
      <div className={styles.container}>
        <div className={styles.topBar}>
          <div className={styles.companyName}>{company_name}</div>
          <div className={styles.recruitPeriod}>
            {start_date} ~ {end_date}
          </div>
        </div>
        <div className={styles.details}>
          <h1>{recruitment_title}</h1>
          {/* 채용 공고 링크 등 상세 정보 */}
        </div>
        <div className={styles.jobGrid}>
          {recruitments &&
            recruitments.map((job) => (
              <div
                key={job.id}
                className={styles.jobCard}
                onClick={() => handleCardClick(job)}
                style={{ cursor: 'pointer' }}
              >
                <div className={styles.jobHeader}>
                  <span className={styles.jobTitle}>{job.title}</span>
                  <span className={styles.jobType}>{job.type}</span>
                </div>
                <div className={styles.jobLink}>
                  <a
                    href={job.link}
                    target="_blank"
                    rel="noreferrer"
                    className={styles.linkAnchor}
                    onClick={(e) => e.stopPropagation()}
                  >
                    채용 공고 사이트 바로가기
                  </a>
                </div>
                <div className={styles.essayList}>
                  {job.essays && job.essays.length > 0 ? (
                    job.essays.map((essay, idx) => (
                      <p
                        key={idx}
                        className={styles.essayItem}
                        data-fulltext={
                          essay.question_text +
                          (essay.limit ? ` (글자수 제한: ${essay.limit})` : '')
                        }
                        onClick={(e) => e.stopPropagation()}
                      >
                        {essay.question_text}
                        {essay.limit && ` (글자수 제한: ${essay.limit})`}
                      </p>
                    ))
                  ) : (
                    <p>자기소개서 문항이 없습니다.</p>
                  )}
                </div>
              </div>
            ))}
        </div>
      </div>
      {showModal && selectedJob && (
        <CoverLetterCreationModal
          recruitJobId={selectedJob.id}
          onClose={handleModalClose}
          onGenerationComplete={handleGenerationComplete}
        />
      )}
      <Footer />
    </>
  );
}

export default CompanyRecruitDetail;
