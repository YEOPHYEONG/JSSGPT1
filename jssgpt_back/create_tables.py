import psycopg2

def create_tables():
    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(
            dbname="jssgpt_db",
            user="jssgpt_user",
            password="jssgpt1!",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        # 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Company (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                industry VARCHAR(255),
                vision TEXT,
                mission TEXT,
                core_values TEXT,
                recent_achievements TEXT,
                key_issues TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Recruitment (
                id SERIAL PRIMARY KEY,
                company_id INTEGER REFERENCES Company(id) ON DELETE CASCADE,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                notes TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS JobInfo (
                id SERIAL PRIMARY KEY,
                recruitment_id INTEGER REFERENCES Recruitment(id) ON DELETE CASCADE,
                job_title VARCHAR(255) NOT NULL,
                job_description TEXT NOT NULL,
                responsibilities TEXT,
                required_skills TEXT,
                soft_skills TEXT,
                key_strengths TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS CoverLetterPrompt (
                id SERIAL PRIMARY KEY,
                job_info_id INTEGER REFERENCES JobInfo(id) ON DELETE CASCADE,
                question_text TEXT NOT NULL,
                outline TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS UserCoverLetter (
                id SERIAL PRIMARY KEY,
                user_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                prompt_id INTEGER REFERENCES CoverLetterPrompt(id) ON DELETE CASCADE,
                resume_file TEXT,
                experience_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'Pending'
            );
        """)

        conn.commit()
        print("Tables created successfully!")
    except Exception as e:
        print("Error creating tables:", e)
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_tables()
