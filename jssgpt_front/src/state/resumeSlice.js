import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { uploadResume, getResumeDetails, deleteResume } from '../services/resumeService';

// Async actions
export const fetchResumeDetails = createAsyncThunk(
  'resume/fetchDetails',
  async () => {
    const data = await getResumeDetails();
    return data;
  }
);

export const uploadResumeFile = createAsyncThunk(
  'resume/upload',
  async (formData) => {
    const data = await uploadResume(formData);
    return data;
  }
);

export const deleteResumeFile = createAsyncThunk('resume/delete', async () => {
  await deleteResume();
});

// Slice
const resumeSlice = createSlice({
  name: 'resume',
  initialState: {
    details: null,
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchResumeDetails.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchResumeDetails.fulfilled, (state, action) => {
        state.loading = false;
        state.details = action.payload;
      })
      .addCase(fetchResumeDetails.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(uploadResumeFile.fulfilled, (state, action) => {
        state.details = action.payload;
      })
      .addCase(deleteResumeFile.fulfilled, (state) => {
        state.details = null;
      });
  },
});

export default resumeSlice.reducer;
