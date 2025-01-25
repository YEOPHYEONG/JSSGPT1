import psycopg2

def insert_company_data():
    try:
        conn = psycopg2.connect(
            dbname="jssgpt_db",
            user="jssgpt_user",
            password="jssgpt1!",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        # 데이터 삽입
        cursor.execute("""
            INSERT INTO Company (company_name, industry, vision, mission, core_values)
            VALUES 
            ('OpenAI', 'Technology', 'To ensure AI benefits all humanity', 
             'Develop safe and beneficial AI', 'Innovation, Safety, Collaboration'),
            ('Tech Corp', 'Finance', 'Empowering businesses with innovative solutions', 
             'Provide world-class financial tools', 'Integrity, Excellence, Customer Focus');
        """)

        conn.commit()
        print("Company data inserted successfully!")
    except Exception as e:
        print("Error inserting data:", e)
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    insert_company_data()
