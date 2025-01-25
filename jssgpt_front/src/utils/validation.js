/**
 * Validates an email address.
 * @param {string} email - The email address to validate
 * @returns {boolean} - True if the email is valid, false otherwise
 */
export const isValidEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };
  
  /**
   * Validates a file size against a maximum size limit.
   * @param {File} file - The file to validate
   * @param {number} maxSizeInMB - The maximum file size in megabytes
   * @returns {boolean} - True if the file size is within the limit, false otherwise
   */
  export const isValidFileSize = (file, maxSizeInMB) => {
    const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
    return file.size <= maxSizeInBytes;
  };
  
  /**
   * Validates if a text exceeds a character limit.
   * @param {string} text - The text to validate
   * @param {number} maxLength - The maximum allowed length
   * @returns {boolean} - True if the text is within the limit, false otherwise
   */
  export const isValidTextLength = (text, maxLength) => {
    return text.length <= maxLength;
  };
  