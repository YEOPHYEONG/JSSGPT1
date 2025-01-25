import api from './api';

/**
 * Generate a draft of the cover letter
 * @param {string} starId - The selected STAR experience ID
 * @param {string} jobDescription - The job description
 * @returns {Promise<string>} Generated cover letter draft
 */
export const generateCoverLetterDraft = async (starId, jobDescription) => {
  try {
    const response = await api.post('/cover-letter/generate', { starId, jobDescription });
    return response.data.draft;
  } catch (error) {
    console.error('Failed to generate cover letter draft:', error);
    throw error;
  }
};

/**
 * Save the final cover letter
 * @param {string} content - The final cover letter content
 * @returns {Promise<void>}
 */
export const saveCoverLetter = async (content) => {
  try {
    await api.post('/cover-letter/save', { content });
  } catch (error) {
    console.error('Failed to save cover letter:', error);
    throw error;
  }
};

/**
 * Fetch the saved cover letter
 * @returns {Promise<string>} The saved cover letter content
 */
export const fetchCoverLetter = async () => {
  try {
    const response = await api.get('/cover-letter');
    return response.data.content;
  } catch (error) {
    console.error('Failed to fetch cover letter:', error);
    throw error;
  }
};
