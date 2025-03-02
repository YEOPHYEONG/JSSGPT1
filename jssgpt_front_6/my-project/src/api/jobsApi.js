// src/api/jobsApi.js
// 실제로는 fetch나 axios로 백엔드에서 데이터를 받아오겠지만,
// 여기서는 간단히 날짜별로 임의 기업 정보가 들어 있는 mock 데이터 예시.

const mockJobs = [
    {
      id: 1,
      date: '2025-02-03',
      companyName: '네이버',
    },
    {
      id: 2,
      date: '2025-02-03',
      companyName: '카카오',
    },
    {
      id: 3,
      date: '2025-02-10',
      companyName: '삼성전자',
    },
    {
      id: 4,
      date: '2025-02-15',
      companyName: 'LG CNS',
    },
  ];
  
  export function getJobs() {
    // 보통은 API 통신: return fetch(...)
    // 여기서는 mock data 반환
    return Promise.resolve(mockJobs);
  }
  