import React, { useEffect, useState } from 'react';
import axios from 'axios';

const CoverLetterCreator = ({ recruitJobId }) => {
    const [prompts, setPrompts] = useState([]);
    const [starExperiences, setStarExperiences] = useState([]);
    const [selectedStars, setSelectedStars] = useState({});
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState({ fetch: false, save: false, generate: false });
    const [generatedDrafts, setGeneratedDrafts] = useState({});

    // 데이터 가져오기
    useEffect(() => {
        const fetchData = async () => {
            setLoading(prev => ({ ...prev, fetch: true }));
            try {
                console.log(`Fetching prompts and STAR experiences for recruitJobId: ${recruitJobId}`);
                const response = await axios.get(`http://localhost:8000/cover-letter/create/${recruitJobId}/`); // API 경로 확인
                setPrompts(response.data.prompts || []);
                setStarExperiences(response.data.star_experiences || []);
                setError(null); // 에러 초기화
            } catch (err) {
                console.error("Error fetching data:", err);
                setError('데이터를 가져오는 중 문제가 발생했습니다.');
            } finally {
                setLoading(prev => ({ ...prev, fetch: false }));
            }
        };
        fetchData();
    }, [recruitJobId]);

    // STAR 경험 선택 핸들러
    const handleStarSelection = (promptId, starId) => {
        setSelectedStars(prev => ({ ...prev, [promptId]: starId }));
    };

    // STAR 경험 저장 요청
    const handleSaveStars = async () => {
        setLoading(prev => ({ ...prev, save: true }));
        try {
            const formData = new FormData();
            for (const [promptId, starId] of Object.entries(selectedStars)) {
                formData.append(`selected_star_${promptId}`, starId);
            }
            await axios.post(`/cover-letter/create/${recruitJobId}/`, formData); // API 경로 확인
            alert('STAR 경험이 저장되었습니다.');
            setError(null);
        } catch (err) {
            console.error("Error saving STAR experiences:", err);
            setError('STAR 경험 저장 중 문제가 발생했습니다.');
        } finally {
            setLoading(prev => ({ ...prev, save: false }));
        }
    };

    // 자기소개서 초안 생성 요청
    const handleGenerateDrafts = async () => {
        setLoading(prev => ({ ...prev, generate: true }));
        try {
            const response = await axios.post(`/cover-letter/generate/${recruitJobId}/`); // API 경로 확인
            setGeneratedDrafts(response.data.drafts || {});
            setError(null);
        } catch (err) {
            console.error("Error generating cover letter drafts:", err);
            setError('초안 생성 중 문제가 발생했습니다.');
        } finally {
            setLoading(prev => ({ ...prev, generate: false }));
        }
    };

    if (error) return <p style={{ color: 'red' }}>{error}</p>;

    return (
        <div>
            <h1>자기소개서 문항</h1>
            {loading.fetch && <p>데이터를 가져오는 중...</p>}
            <ul>
                {prompts.map(prompt => (
                    <li key={prompt.id}>
                        <h3>{prompt.question_text}</h3>
                        <p>추천 주제: {prompt.outline}</p>
                        <select
                            value={selectedStars[prompt.id] || ''}
                            onChange={e => handleStarSelection(prompt.id, e.target.value)}
                        >
                            <option value="">STAR 경험 선택</option>
                            {starExperiences.map(star => (
                                <option key={star.id} value={star.id}>
                                    {star.title}
                                </option>
                            ))}
                        </select>
                    </li>
                ))}
            </ul>
            <button onClick={handleSaveStars} disabled={loading.save}>
                {loading.save ? '저장 중...' : 'STAR 경험 저장'}
            </button>
            <button onClick={handleGenerateDrafts} disabled={loading.generate}>
                {loading.generate ? '생성 중...' : '자기소개서 초안 생성'}
            </button>
            {Object.keys(generatedDrafts).length > 0 && (
                <div>
                    <h2>생성된 초안</h2>
                    <ul>
                        {Object.entries(generatedDrafts).map(([promptId, content]) => (
                            <li key={promptId}>
                                <h3>{prompts.find(p => p.id === parseInt(promptId))?.question_text}</h3>
                                <p>{content}</p>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default CoverLetterCreator;
