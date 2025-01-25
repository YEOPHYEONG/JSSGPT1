import api from './api';

/**
 * Upload resume file
 * @param {FormData} formData - The FormData containing the uploaded file
 * @returns {Promise<object>} The response from the server
 */
export const uploadResume = async (formData) => {
  try {
    const response = await api.post('/resume/upload', formData);
    return response.data;
  } catch (error) {
    console.error('Failed to upload resume:', error);
    throw error;
  }
};

/**
 * Fetch uploaded resume details
 * @returns {Promise<object>} The uploaded resume details
 */
export const getResumeDetails = async () => {
  try {
    const response = await api.get('/resume/details');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch resume details:', error);
    throw error;
  }
};

/**
 * Delete uploaded resume
 * @returns {Promise<void>}
 */
export const deleteResume = async () => {
  try {
    await api.delete('/resume/delete');
  } catch (error) {
    console.error('Failed to delete resume:', error);
    throw error;
  }
};
