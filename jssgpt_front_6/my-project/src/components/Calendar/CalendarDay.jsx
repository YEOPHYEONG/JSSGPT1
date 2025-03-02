// src/components/Calendar/CalendarDay.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import classNames from 'classnames';
import styles from './CalendarDay.module.css';

function CalendarDay({ day, events }) {
  const navigate = useNavigate();
  const dayNumber = day.date();
  const formatted = day.format('YYYY-MM-DD');
  const isToday = dayjs().isSame(day, 'day');

  // 부모 컨테이너 클릭 로그 (디버깅 용)
  const handleCellClick = () => {
    console.log(`Day cell clicked: ${formatted}`);
  };

  // 이벤트 클릭 핸들러: e.preventDefault()와 e.stopPropagation() 추가
  const handleEventClick = (e, event) => {
    e.preventDefault();
    e.stopPropagation();
    console.log("Event clicked:", event);
    navigate(`/company/${encodeURIComponent(event.company_name)}/${event.recruitment_id}`);
  };

  return (
    <div
      className={classNames(styles.dayCell, {
        [styles.todayCell]: isToday,
      })}
      onClick={handleCellClick} // 부모 클릭 이벤트 디버깅
    >
      <div className={styles.dateLabel}>{dayNumber}</div>
      {events && events.map((event) => {
        const isStart = formatted === event.start_date;
        const isEnd = formatted === event.end_date;
        const textColor = isStart ? 'green' : isEnd ? 'red' : '#ffffff';
        return (
          <div
            key={event.recruitment_id}
            className={styles.jobItem}
            style={{ color: textColor, cursor: 'pointer' }}
            onClick={(e) => handleEventClick(e, event)}
          >
            {event.company_name}
          </div>
        );
      })}
    </div>
  );
}

export default CalendarDay;
