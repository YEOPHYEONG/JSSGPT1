/**
 * Reads the content of a file as text.
 * @param {File} file - The file to read
 * @returns {Promise<string>} - The file content as a string
 */
export const readFileAsText = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
  
      reader.onload = (event) => {
        resolve(event.target.result);
      };
  
      reader.onerror = (error) => {
        reject(error);
      };
  
      reader.readAsText(file);
    });
  };
  
  /**
   * Reads the content of a file as a Data URL (e.g., for previewing images).
   * @param {File} file - The file to read
   * @returns {Promise<string>} - The file content as a Data URL
   */
  export const readFileAsDataURL = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
  
      reader.onload = (event) => {
        resolve(event.target.result);
      };
  
      reader.onerror = (error) => {
        reject(error);
      };
  
      reader.readAsDataURL(file);
    });
  };
  