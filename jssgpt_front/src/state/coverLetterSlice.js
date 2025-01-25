import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { generateCoverLetterDraft, saveCoverLetter, fetchCoverLetter } from '../services/coverLetterService';

// Async actions
export const fetchCoverLetterContent = createAsyncThunk(
  'coverLetter/fetch',
  async () => {
    const content = await fetchCoverLetter();
    return content;
  }
);

export const generateDraft = createAsyncThunk(
  'coverLetter/generateDraft',
  async ({ starId, jobDescription }) => {
    const draft = await generateCoverLetterDraft(starId, jobDescription);
    return draft;
  }
);

export const saveCoverLetterContent = createAsyncThunk(
  'coverLetter/save',
  async (content) => {
    await saveCoverLetter(content);
    return content;
  }
);

// Slice
const coverLetterSlice = createSlice({
  name: 'coverLetter',
  initialState: {
    content: '',
    draft: '',
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchCoverLetterContent.fulfilled, (state, action) => {
        state.content = action.payload;
      })
      .addCase(generateDraft.fulfilled, (state, action) => {
        state.draft = action.payload;
      })
      .addCase(saveCoverLetterContent.fulfilled, (state, action) => {
        state.content = action.payload;
      });
  },
});

export default coverLetterSlice.reducer;
