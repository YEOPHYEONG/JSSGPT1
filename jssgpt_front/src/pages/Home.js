import React, { useState } from 'react';
import {
  Grid2,
  Box,
  Typography,
  TextField,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
} from '@mui/material';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css'; // 캘린더 스타일 추가
import StarIcon from '@mui/icons-material/Star'; // 관심기업 아이콘
import Header from '../components/Navigation/Header';
import ChatSection from '../components/ChatSection';

const Home = () => {
  // 샘플 채용 데이터 (날짜별 공고 데이터)
  const jobData = {
    '2024-12-28': [
      { id: 1, name: '네이버', type: '채', position: '개발자', status: '진행 중' },
      { id: 2, name: '카카오', type: '끝', position: '디자이너', status: '마감' },
    ],
    '2024-12-29': [
      { id: 3, name: '삼성전자', type: '채', position: '마케팅', status: '진행 중' },
    ],
  };

  const [selectedDate, setSelectedDate] = useState(new Date());
  const [searchQuery, setSearchQuery] = useState('');
  const [popupData, setPopupData] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [favoriteCompanies, setFavoriteCompanies] = useState(['한화시멘트', '카카오', '네이버']);

  // 날짜 선택 시 팝업 데이터 업데이트
  const handleDateClick = (date) => {
    const formattedDate = date.toISOString().split('T')[0];
    setPopupData(jobData[formattedDate] || []);
    setIsDialogOpen(true);
  };

  // 관심 기업 추가
  const handleFavoriteClick = (company) => {
    if (!favoriteCompanies.includes(company)) {
      setFavoriteCompanies([...favoriteCompanies, company]);
    }
  };

  // 검색 결과
  const filteredJobs = popupData.filter((job) =>
    job.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      <Header />
      <Box sx={{ flexGrow: 1, padding: 2 }}>
        {/* 검색창 */}
        <Box sx={{ marginBottom: 2 }}>
          <TextField
            fullWidth
            label="기업명을 검색하세요"
            variant="outlined"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </Box>
        <Grid2 container spacing={2}>
          {/* 채용 공고 달력 */}
          <Grid2 item xs={3}>
            <Box sx={{ border: '1px solid #ddd', borderRadius: '8px', padding: 2 }}>
              <Typography variant="h6" gutterBottom>
                달력
              </Typography>
              <Calendar
                onClickDay={handleDateClick}
                tileContent={({ date, view }) => {
                  const formattedDate = date.toISOString().split('T')[0];
                  const jobs = jobData[formattedDate] || [];
                  return (
                    <div style={{ fontSize: '0.8rem', textAlign: 'center' }}>
                      {jobs.map((job) => (
                        <div key={job.id}>
                          <span style={{ color: job.type === '채' ? 'green' : 'red' }}>{job.type}</span> {job.name}
                        </div>
                      ))}
                    </div>
                  );
                }}
              />
            </Box>
          </Grid2>

          {/* 채용 공고 리스트 */}
          <Grid2 item xs={5}>
            <Box sx={{ border: '1px solid #ddd', borderRadius: '8px', padding: 2 }}>
              <Typography variant="h6" gutterBottom>
                채용 공고
              </Typography>
              <List>
                {filteredJobs.length > 0 ? (
                  filteredJobs.map((job) => (
                    <ListItem key={job.id} sx={{ borderBottom: '1px solid #ddd' }}>
                      <ListItemText
                        primary={`${job.name} - ${job.position}`}
                        secondary={`상태: ${job.status}`}
                      />
                      <IconButton onClick={() => handleFavoriteClick(job.name)}>
                        <StarIcon color="primary" />
                      </IconButton>
                    </ListItem>
                  ))
                ) : (
                  <Typography>해당 날짜에 공고가 없습니다.</Typography>
                )}
              </List>
            </Box>
          </Grid2>

          {/* 관심 기업 */}
          <Grid2 item xs={4}>
            <Box sx={{ border: '1px solid #ddd', borderRadius: '8px', padding: 2 }}>
              <Typography variant="h6" gutterBottom>
                관심 기업
              </Typography>
              <List>
                {favoriteCompanies.map((company, index) => (
                  <ListItem key={index} sx={{ borderBottom: '1px solid #ddd' }}>
                    <ListItemText primary={company} />
                  </ListItem>
                ))}
              </List>
            </Box>
          </Grid2>
        </Grid2>
      </Box>

      {/* 팝업 다이얼로그 */}
      <Dialog open={isDialogOpen} onClose={() => setIsDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>채용 공고 상세</DialogTitle>
        <DialogContent>
          <List>
            {popupData.map((job) => (
              <ListItem key={job.id} sx={{ borderBottom: '1px solid #ddd' }}>
                <ListItemText
                  primary={`${job.name} - ${job.position}`}
                  secondary={`상태: ${job.status}`}
                />
                <IconButton onClick={() => handleFavoriteClick(job.name)}>
                  <StarIcon color="primary" />
                </IconButton>
              </ListItem>
            ))}
          </List>
        </DialogContent>
      </Dialog>

      <ChatSection />
    </>
  );
};

export default Home;
