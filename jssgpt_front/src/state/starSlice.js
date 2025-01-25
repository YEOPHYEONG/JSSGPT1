import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { fetchStarExperiences, fetchStarRecommendation, saveStarSelection } from '../services/starService';

// Async actions
export const fetchAllStarExperiences = createAsyncThunk(
  'star/fetchAll',
  async () => {
    const data = await fetchStarExperiences();
    return data;
  }
);

export const fetchStarRecommendationAsync = createAsyncThunk(
  'star/fetchRecommendation',
  async () => {
    const data = await fetchStarRecommendation();
    return data;
  }
);

export const saveSelectedStar = createAsyncThunk(
  'star/saveSelection',
  async (starId) => {
    await saveStarSelection(starId);
    return starId;
  }
);

// Slice
const starSlice = createSlice({
  name: 'star',
  initialState: {
    experiences: [],
    recommendation: null,
    selectedStar: null,
    loading: false,
    error: null,
  },
  reducers: {
    setSelectedStar(state, action) {
      state.selectedStar = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAllStarExperiences.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAllStarExperiences.fulfilled, (state, action) => {
        state.loading = false;
        state.experiences = action.payload;
      })
      .addCase(fetchAllStarExperiences.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(fetchStarRecommendationAsync.fulfilled, (state, action) => {
        state.recommendation = action.payload;
      })
      .addCase(saveSelectedStar.fulfilled, (state, action) => {
        state.selectedStar = action.payload;
      });
  },
});

export const { setSelectedStar } = starSlice.actions;

export default starSlice.reducer;
