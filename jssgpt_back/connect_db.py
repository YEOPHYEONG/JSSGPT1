import psycopg2

def connect_to_db():
    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(
            dbname="jssgpt_db",       # 데이터베이스 이름
            user="jssgpt_user",       # 사용자 이름
            password="jssgpt1!",      # 비밀번호
            host="localhost",         # 호스트
            port="5432"               # 포트
        )
        print("Database connection successful!")  # 연결 성공 메시지 출력
        conn.close()
    except Exception as e:
        print("Error connecting to the database:", e)  # 오류 발생 시 메시지 출력

# 함수 실행
if __name__ == "__main__":
    connect_to_db()
