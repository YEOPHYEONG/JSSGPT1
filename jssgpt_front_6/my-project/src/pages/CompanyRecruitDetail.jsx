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
        setRecruitData(response.data);
      } catch (err) {
        setError(err);
      }
    }
    fetchDetail();
  }, [recruitmentId]);

  const handleCardClick = async (job) => {
    try {
      const response = await axios.get(
        `/api/cover-letter/get/?recruit_job_id=${job.id}`,
        { withCredentials: true }
      );

      if (Object.keys(response.data).length === 0) {
        setSelectedJob(job);
        setShowModal(true);
      } else {
        navigate('/essay', {
          state: {
            companyName: recruitData.company_name,
            recruitmentTitle: job.title,
            questions: job.essays,
            recruitJobId: job.id,
          },
        });
      }
    } catch (error) {
      console.error("Error checking cover letter existence:", error);
    }
  };

  const handleModalClose = () => setShowModal(false);

  const handleGenerationComplete = () => {
    setShowModal(false);
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
      <main className={styles.container}>

        {/* ✅ 상단바 개선 */}
        <section className={styles.topBar}>
          <h1 className={styles.companyName}>📆 {company_name} 📆</h1>
          <p className={styles.recruitPeriod}> 채용기간: {start_date} ~ {end_date}</p>
        </section>

        <section className={styles.mainBox}>
          <h2 className={styles.details}>{recruitment_title}</h2>

          <section className={styles.jobGrid}>
            {recruitments?.map((job) => (
              <div
                key={job.id}
                className={styles.jobCard}
                onClick={() => handleCardClick(job)}
              >
                {/* ✅ hover 멘트 */}
                <div className={styles.hoverMessage}
                onClick={(e) => {
    // 부모의 onClick 이벤트가 중복 실행되지 않도록 전파를 막음
    e.stopPropagation();
    // jobCard 클릭 시와 동일하게 handleCardClick 호출
    handleCardClick(job);
  }}
>                
                  자기소개서 작성!</div>

                <header className={styles.jobHeader}>
                  <h3 className={styles.jobTitle}>{job.title}</h3>
                  <span className={styles.jobType}>{job.type}</span>
                </header>

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
                  {job.essays?.length > 0 ? (
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
                       📝 {essay.question_text}
                        {essay.limit && ` (글자수 제한: ${essay.limit})`}
                      </p>
                    ))
                  ) : (
                    <p className={styles.essayItem}>자기소개서 문항이 없습니다.</p>
                  )}
                </div>
              </div>
            ))}
          </section>
        </section>
      </main>

      {showModal && selectedJob && (
        <CoverLetterCreationModal
          recruitJobId={selectedJob.id}
          onClose={handleModalClose}
          onGenerationComplete={handleGenerationComplete}
        />
      )}
      
      {/* ✅ 플로팅 버튼 추가 */}
<button
  className={styles.floatingButton}
  onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
>
  TOP
</button>

      <Footer />
    </>
  );
}

export default CompanyRecruitDetail;
