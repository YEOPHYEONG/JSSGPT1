import React from 'react';
import { useParams } from 'react-router-dom'; // useParams 가져오기
import CoverLetterCreator from '../components/CoverLetter/CoverLetterCreator';

const CoverLetterPage = () => {
    // useParams를 사용하여 URL 매개변수 가져오기
    const { recruitJobId } = useParams();

    return (
        <div className="cover-letter-page">
            <h1>Cover Letter for Job ID: {recruitJobId}</h1>
            <CoverLetterCreator recruitJobId={recruitJobId} />
        </div>
    );
};

export default CoverLetterPage;
