import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';
import styles from './Header.module.css';
import { getCookie } from '../../utils/utils';

function Header({ onLogoClick }) {
  const navigate = useNavigate();
  const { user, logout } = useContext(AuthContext);
  const [isProfileOpen, setProfileOpen] = useState(false);

  const handleLogoClick = () => {
    if (onLogoClick) {
      onLogoClick();
    } else {
      navigate('/');
    }
  };

  const toggleProfileMenu = () => {
    setProfileOpen((prev) => !prev);
  };

  const handleLogout = async () => {
    try {
      const csrfToken = getCookie('csrftoken');
      const response = await fetch('/api/auth/logout/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': csrfToken,
        },
      });
      if (response.ok) {
        logout();
        navigate('/');
      } else {
        console.error("Logout failed", response.statusText);
      }
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  return (
    <header className={styles.header}>
      <div className={styles.logo} onClick={handleLogoClick}>
        <img
          src="/assets/JSSGPT_header_black.svg"
          alt="JSSGPT"
          className={styles.logoImage}
        />
      </div>
      <div className={styles.profileArea}>
        {/* 이력서 업로드 버튼 추가 (프로필 아이콘 왼쪽) */}
        <button
          type="button"
          className={styles.uploadResumeButton}
          onClick={() => navigate('/upload-resume')}
        >
          이력서 업로드
        </button>
        <button
          type="button"
          className={styles.profileButton}
          onClick={toggleProfileMenu}
        >
          <img
            src="/assets/new-profile-icon.png"
            alt="New Profile Icon"
            className={styles.profileIcon}
          />
        </button>
        {isProfileOpen && (
          <div className={styles.dropdownMenu}>
            {user ? (
              <>
                <div className={styles.email}>{user.email}</div>
                <button
                  className={styles.menuItem}
                  onClick={() => navigate('/cover-letter')}
                >
                  내 자기소개서 관리
                </button>
                <button
                  className={styles.menuItem}
                  onClick={() => navigate('/experience-edit')}
                >
                  내 경험관리
                </button>
                <button className={styles.menuItem} onClick={handleLogout}>
                  로그아웃
                </button>
              </>
            ) : (
              <div
                className={styles.loginPrompt}
                onClick={() => navigate('/login')}
                style={{ cursor: 'pointer' }}
              >
                로그인해주세요
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;
