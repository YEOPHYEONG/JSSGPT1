import React, { useState } from 'react';
import { Box, Typography } from '@mui/material';
import StarList from '../components/StarExperience/StarList';
import StarSelector from '../components/StarExperience/StarSelector';
import StarRecommendation from '../components/StarExperience/StarRecommendation';

/**
 * STAR Experience Page
 */
const StarExperience = () => {
  const [stars, setStars] = useState([
    { id: '1', title: 'Project Management', description: 'Managed a team to deliver a project on time.' },
    { id: '2', title: 'Data Analysis', description: 'Analyzed complex datasets to provide insights.' },
    { id: '3', title: 'Customer Service', description: 'Resolved client issues and improved satisfaction.' },
  ]);
  const [selectedStar, setSelectedStar] = useState('');
  const [recommendation, setRecommendation] = useState({
    id: '2',
    title: 'Data Analysis',
    description: 'Analyzed complex datasets to provide insights.',
  });

  const handleSelect = (starId) => {
    setSelectedStar(starId);
  };

  const handleAcceptRecommendation = () => {
    setSelectedStar(recommendation.id);
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        STAR Experience Management
      </Typography>
      <StarList stars={stars} />
      <StarSelector stars={stars} selectedStar={selectedStar} onSelect={handleSelect} />
      <StarRecommendation recommendation={recommendation} onAccept={handleAcceptRecommendation} />
    </Box>
  );
};

export default StarExperience;
