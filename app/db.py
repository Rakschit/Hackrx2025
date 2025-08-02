import os
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.getenv("DATABASE_URL")

def insert_hackrx_log(file_id, file_link, questions_json, answers_json, total_time_ms, timings_json):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    execute_values(
        cur,
        """
        INSERT INTO qa_logs (file_id, file_link, questions, answers, total_time_ms, timings)
        VALUES %s
        """,
        [(file_id, file_link, questions_json, answers_json, total_time_ms, timings_json)]
    )

    conn.commit()
    cur.close()
    conn.close()
