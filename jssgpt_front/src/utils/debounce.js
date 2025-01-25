/**
 * Creates a debounced function that delays invoking the provided function until after the specified wait time has elapsed.
 * @param {function} func - The function to debounce
 * @param {number} wait - The number of milliseconds to delay
 * @returns {function} - The debounced function
 */
export const debounce = (func, wait) => {
    let timeout;
  
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  };
  