// src/components/Calendar/Calendar.jsx
import React, { useState, useEffect } from 'react';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import styles from './Calendar.module.css';
import CalendarDay from './CalendarDay';
import axios from 'axios';

dayjs.extend(utc);

function Calendar() {
  // 기본 currentDate: 현재 UTC 날짜
  const [currentDate, setCurrentDate] = useState(dayjs.utc());
  const [recruitmentEvents, setRecruitmentEvents] = useState([]);

  useEffect(() => {
    async function fetchEvents() {
      try {
        const response = await axios.get('/api/recruitment-events/');
        console.log("API Response:", response.data);
        setRecruitmentEvents(response.data);
      } catch (error) {
        console.error("Failed to fetch recruitment events:", error);
      }
    }
    fetchEvents();
  }, []);

  const handlePrevMonth = () => {
    setCurrentDate(prev => prev.subtract(1, 'month'));
  };
  const handleNextMonth = () => {
    setCurrentDate(prev => prev.add(1, 'month'));
  };

  const startOfMonth = currentDate.startOf('month');
  const endOfMonth = currentDate.endOf('month');

  // 달력 그리드를 현재 달의 시작 주 일요일부터 마지막 주 토요일까지 포함 (UTC 기준)
  const calendarStart = startOfMonth.startOf('week');
  const calendarEnd = endOfMonth.endOf('week');

  const daysArray = [];
  let day = calendarStart;
  while (day.isBefore(calendarEnd) || day.isSame(calendarEnd, 'day')) {
    daysArray.push(day.clone());
    day = day.add(1, 'day');
  }

  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  return (
    <div className={styles.calendarWrapper}>
      <div className={styles.calendarContainer}>
        <div className={styles.calendarHeader}>
          <button onClick={handlePrevMonth} className={styles.monthNavBtn}>
            &lt;
          </button>
          <span className={styles.monthLabel}>
            {currentDate.format('YYYY년 M월')}
          </span>
          <button onClick={handleNextMonth} className={styles.monthNavBtn}>
            &gt;
          </button>
        </div>
        <div className={styles.weekDays}>
          {weekDays.map(wd => (
            <div key={wd} className={styles.weekDay}>
              {wd}
            </div>
          ))}
        </div>
        <div className={styles.calendarGrid}>
          {daysArray.map(dayItem => {
            const formatted = dayItem.format('YYYY-MM-DD');
            // 이벤트 필터링: 오직 시작일과 종료일에 해당하는 날짜만 반환
            const eventsForDay = recruitmentEvents.filter(event => {
              const isStart = formatted === event.start_date;
              const isEnd = formatted === event.end_date;
              const result = isStart || isEnd;
              console.log(
                `Checking day ${formatted}: event (${event.company_name}) with start ${event.start_date} and end ${event.end_date} => result: ${result}`
              );
              return result;
            });
            console.log(`For day ${formatted}, found events:`, eventsForDay);
            return (
              <CalendarDay
                key={formatted}
                day={dayItem}
                events={eventsForDay}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default Calendar;
