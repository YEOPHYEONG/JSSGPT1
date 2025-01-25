import { useEffect, useState } from 'react';

/**
 * Custom hook to autosave data after a specified delay
 * @param {any} value - The value to autosave
 * @param {function} saveFunction - Function to handle the save process
 * @param {number} delay - The delay in milliseconds before saving
 */
const useAutosave = (value, saveFunction, delay = 2000) => {
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (value === null || value === undefined) return;

    const handler = setTimeout(async () => {
      setIsSaving(true);
      await saveFunction(value);
      setIsSaving(false);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, saveFunction, delay]);

  return isSaving;
};

export default useAutosave;
