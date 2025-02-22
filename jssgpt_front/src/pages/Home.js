import React, { useState, useEffect } from 'react';
import { FaUserCircle } from 'react-icons/fa'; // 아이콘 예시 (react-icons)
import { MdKeyboardArrowLeft, MdKeyboardArrowRight } from 'react-icons/md'; // 월 이동 아이콘 예시
import { useNavigate } from 'react-router-dom'; // 라우팅 라이브러리 예시

/**
 * HomePage.jsx
 * 채용공고달력을 표시하는 메인 홈 페이지 예시
 */
function HomePage() {
  // 오늘 날짜 정보
  const today = new Date();
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(today.getMonth()); // 0부터 시작(0: 1월, 1: 2월, ...)
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  const navigate = useNavigate(); // react-router-dom 사용 시

  // 실제로는 백엔드에서 받아온 채용 이벤트 정보를 저장하는 예시
  // date 문자열 포맷은 "YYYY-MM-DD" 등으로 통일해두고, 실제 날짜와 매칭 시켜 사용
  const [recruitEvents, setRecruitEvents] = useState([
    {
      date: '2025-02-02',
      companies: [
        { id: 1, name: 'Company A' },
        { id: 2, name: 'Company B' },
      ],
    },
    {
      date: '2025-02-05',
      companies: [
        { id: 3, name: 'Company C' },
      ],
    },
    {
      date: '2025-02-15',
      companies: [
        { id: 4, name: 'Company D' },
        { id: 5, name: 'Company E' },
        { id: 6, name: 'Company F' },
      ],
    },
  ]);

  // 현재 달의 첫째 날과 마지막 날 구하기
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1);
  const lastDayOfMonth = new Date(currentYear, currentMonth + 1, 0);
  
  // 달력에 표시할 일(day) 배열
  // (이 예시에서는 일요일 시작 ~ 토요일 종료 형태를 간단히 표현)
  // 실제로는 지역/요일 시작 요건에 맞춰 로직 수정 가능
  const calendarDays = [];
  
  // 이번 달 첫째 날의 요일 인덱스(0:일, 1:월, 2:화, ...)
  const startDayIndex = firstDayOfMonth.getDay();
  // 이번 달의 총 일 수
  const totalDaysInMonth = lastDayOfMonth.getDate();
  
  // 1) 첫째 주에서 이전 달 날짜(공백) 채우기
  for (let i = 0; i < startDayIndex; i++) {
    calendarDays.push(null); // null로 채워서 빈 칸 처리
  }
  // 2) 이번 달 날짜 채우기
  for (let day = 1; day <= totalDaysInMonth; day++) {
    calendarDays.push(day);
  }

  // 이전 달로 이동
  const handlePrevMonth = () => {
    if (currentMonth === 0) {
      // 현재 1월이면 이전 달은 작년 12월
      setCurrentYear(currentYear - 1);
      setCurrentMonth(11);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  // 다음 달로 이동
  const handleNextMonth = () => {
    if (currentMonth === 11) {
      // 현재 12월이면 다음 달은 내년 1월
      setCurrentYear(currentYear + 1);
      setCurrentMonth(0);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  // 회사명 클릭 시 해당 채용공고 페이지로 이동 (예시)
  const handleCompanyClick = (companyId) => {
    // 예: /job/1 형태로 이동
    navigate(`/job/${companyId}`);
  };

  // 프로필 아이콘 클릭 시 드롭다운 토글
  const toggleProfileDropdown = () => {
    setShowProfileDropdown(!showProfileDropdown);
  };

  // 드롭다운 메뉴 클릭 시 기능 (예시)
  const handleProfileMenuClick = (menu) => {
    switch (menu) {
      case 'introduction':
        // 내 자기소개서 관리 페이지로 이동
        navigate('/profile/introduction');
        break;
      case 'experience':
        // 내 경험 관리 페이지로 이동
        navigate('/profile/experience');
        break;
      case 'logout':
        // 로그아웃 처리 후 홈으로
        alert('로그아웃 되었습니다.');
        navigate('/');
        break;
      default:
        break;
    }
    setShowProfileDropdown(false);
  };

  // 로고 클릭 시 홈 이동 & 새로고침(예시)
  const handleLogoClick = () => {
    navigate('/');
    window.location.reload(); // 새로고침
  };

  // 현재 연도/월을 문자열로 표시(월은 0부터 시작하므로 +1)
  const displayMonth = currentMonth + 1;

  return (
    <div className="flex flex-col min-h-screen bg-gray-900 text-white">
      {/* 헤더 */}
      <header className="w-full bg-teal-700 p-4 flex items-center justify-between">
        {/* 1-1. 헤더 로고 */}
        <div
          className="text-2xl font-bold cursor-pointer"
          onClick={handleLogoClick}
        >
          JSSGPT
        </div>

        {/* 1-2. 프로필 아이콘 */}
        <div className="relative">
          <FaUserCircle
            className="text-3xl cursor-pointer"
            onClick={toggleProfileDropdown}
          />
          {showProfileDropdown && (
            <div className="absolute right-0 mt-2 w-48 bg-white text-black rounded shadow-md py-2 z-50">
              <div className="px-4 py-2 border-b">
                {/* 가입 이메일 표시 (예시) */}
                <p className="text-sm text-gray-600">user@example.com</p>
              </div>
              <button
                className="w-full text-left px-4 py-2 hover:bg-gray-100"
                onClick={() => handleProfileMenuClick('introduction')}
              >
                내 자기소개서 관리
              </button>
              <button
                className="w-full text-left px-4 py-2 hover:bg-gray-100"
                onClick={() => handleProfileMenuClick('experience')}
              >
                내 경험관리
              </button>
              <button
                className="w-full text-left px-4 py-2 hover:bg-gray-100"
                onClick={() => handleProfileMenuClick('logout')}
              >
                로그아웃
              </button>
            </div>
          )}
        </div>
      </header>

      {/* 메인 컨텐츠 - 채용 달력 */}
      <main className="flex-grow bg-gray-800 p-4">
        <div className="max-w-5xl mx-auto bg-teal-600 p-4 rounded-md">
          {/* 2-1. 상단 월 표시 및 월 이동 아이콘 */}
          <div className="flex items-center justify-center mb-4 text-xl font-semibold text-center text-white">
            <button
              onClick={handlePrevMonth}
              className="mr-4 hover:text-gray-300"
            >
              <MdKeyboardArrowLeft size={24} />
            </button>
            <div>
              {currentYear}년 {displayMonth}월
            </div>
            <button
              onClick={handleNextMonth}
              className="ml-4 hover:text-gray-300"
            >
              <MdKeyboardArrowRight size={24} />
            </button>
          </div>

          {/* 2-2. 캘린더 */}
          <div className="overflow-x-auto">
            {/* 요일 헤더 */}
            <div className="grid grid-cols-7 text-center font-semibold text-white mb-2">
              <div>일</div>
              <div>월</div>
              <div>화</div>
              <div>수</div>
              <div>목</div>
              <div>금</div>
              <div>토</div>
            </div>

            {/* 날짜 영역 (7열 그리드) */}
            <div className="grid grid-cols-7 gap-1">
              {calendarDays.map((day, idx) => {
                // 실제 날짜 객체 (year, month, day)
                // day가 null이면 이전 달 공백
                let dateString = null;
                if (day) {
                  // 월은 0부터 시작하므로 +1
                  const mm = (currentMonth + 1).toString().padStart(2, '0');
                  const dd = day.toString().padStart(2, '0');
                  dateString = `${currentYear}-${mm}-${dd}`;
                }

                // recruitEvents 배열에서 해당 날짜에 맞는 이벤트 찾기
                const eventForDay = recruitEvents.find(
                  (event) => event.date === dateString
                );

                return (
                  <div
                    key={idx}
                    className={`flex flex-col border border-gray-700 h-28 p-1 bg-teal-500 text-white overflow-auto`}
                  >
                    {/* 날짜 숫자 표시 */}
                    <div className="font-bold mb-1">
                      {day ? day : ''}
                    </div>
                    {/* 기업 리스트 표시 */}
                    {eventForDay &&
                      eventForDay.companies.map((company) => (
                        <button
                          key={company.id}
                          className="text-left text-sm bg-teal-700 hover:bg-teal-900 w-full mb-1 rounded px-1"
                          onClick={() => handleCompanyClick(company.id)}
                        >
                          {company.name}
                        </button>
                      ))}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </main>

      {/* 푸터 */}
      <footer className="w-full bg-teal-700 p-4 text-center">
        <p>© 2025 JSSGPT. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default HomePage;
