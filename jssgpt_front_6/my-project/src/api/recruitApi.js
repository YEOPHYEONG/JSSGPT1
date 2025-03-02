// src/api/recruitApi.js

const mockRecruitData = [
    {
      company_name: '카카오',
      start_date: '2025-02-10',
      end_date: '2025-02-25',
      recruitments: [
        {
          id: 1,
          title: '리스크관리',
          link: 'http://127.0.0.1:5173/job/1',
          type: '경력, 수시채용',
          essays: [
            '지원 동기 및 포부(1000자)',
            '핵심 역량 혹은 강점을 상세하게 서술해주세요. (150자)',
          ],
        },
        {
          id: 2,
          title: 'IB업무지원',
          link: 'https://recruit.kakao.com/job/2',
          type: '인턴',
          essays: [
            'IB 업무 관련 경험(500자)',
            '팀 프로젝트 협업 경험(300자)',
          ],
        },
      ],
    },
    {
      company_name: '네이버',
      start_date: '2025-03-01',
      end_date: '2025-03-20',
      recruitments: [
        {
          id: 1,
          title: '프론트엔드 개발',
          link: 'https://recruit.naver.com/job/fe',
          type: '신입, 공개채용',
          essays: [
            '프론트엔드 개발 역량(1000자)',
            '팀 프로젝트에서 맡은 역할(500자)',
          ],
        },
      ],
    },
  ];
  
  // 특정 companyName으로 검색해 데이터 반환
  export function getCompanyRecruit(companyName) {
    const found = mockRecruitData.find(
      (item) => item.company_name === companyName,
    );
    return Promise.resolve(found || null);
  }
  