import api from './api';

/**
 * Fetch all STAR experiences
 * @returns {Promise<array>} List of STAR experiences
 */
export const fetchStarExperiences = async () => {
  try {
    const response = await api.get('/star/experiences');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch STAR experiences:', error);
    throw error;
  }
};

/**
 * Fetch recommended STAR experience
 * @returns {Promise<object>} The recommended STAR experience
 */
export const fetchStarRecommendation = async () => {
  try {
    const response = await api.get('/star/recommendation');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch STAR recommendation:', error);
    throw error;
  }
};

/**
 * Save STAR experience selection
 * @param {string} starId - The ID of the selected STAR experience
 * @returns {Promise<void>}
 */
export const saveStarSelection = async (starId) => {
  try {
    await api.post('/star/save-selection', { starId });
  } catch (error) {
    console.error('Failed to save STAR selection:', error);
    throw error;
  }
};
