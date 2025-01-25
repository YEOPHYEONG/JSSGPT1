import { configureStore } from '@reduxjs/toolkit';
import resumeReducer from './resumeSlice';
import starReducer from './starSlice';
import coverLetterReducer from './coverLetterSlice';

const store = configureStore({
  reducer: {
    resume: resumeReducer,
    star: starReducer,
    coverLetter: coverLetterReducer,
  },
});

export default store;
