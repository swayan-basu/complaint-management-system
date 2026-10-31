import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "complaint_db")

REQUIRED_COLUMNS = {
    "name": "VARCHAR(255) NOT NULL",
    "email": "VARCHAR(255) NOT NULL",
    "category": "VARCHAR(100) NOT NULL DEFAULT 'General feedback'",
    "urgency": "ENUM('low','medium','high') NOT NULL DEFAULT 'low'",
    "message": "TEXT NOT NULL",
    "status": "VARCHAR(20) NOT NULL DEFAULT 'pending'",
    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
}


def _is_valid_column_name(col):
    """Validate column name to prevent SQL injection."""
    import re
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col))


def ensure_schema(cursor):
    cursor.execute("SHOW COLUMNS FROM complaints")
    existing = {row[0] for row in cursor.fetchall()}

    if "ref" not in existing:
        cursor.execute("ALTER TABLE complaints ADD COLUMN ref VARCHAR(32) NULL")
        existing.add("ref")

    if "complaint" in existing and "message" not in existing:
        cursor.execute("ALTER TABLE complaints CHANGE complaint message TEXT NOT NULL")
        existing.remove("complaint")
        existing.add("message")

    if "timestamp" in existing and "created_at" not in existing:
        cursor.execute("ALTER TABLE complaints CHANGE timestamp created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        existing.remove("timestamp")
        existing.add("created_at")

    for col, definition in REQUIRED_COLUMNS.items():
        if col not in existing and _is_valid_column_name(col):
            cursor.execute(f"ALTER TABLE complaints ADD COLUMN {col} {definition}")

    cursor.execute("UPDATE complaints SET status = 'pending' WHERE status IS NULL OR TRIM(status) = ''")
    cursor.execute("UPDATE complaints SET status = 'pending' WHERE LOWER(TRIM(status)) = 'pending'")
    cursor.execute("UPDATE complaints SET status = 'under review' WHERE LOWER(TRIM(status)) IN ('under review', 'under_review', 'in review')")
    cursor.execute("UPDATE complaints SET status = 'resolved' WHERE LOWER(TRIM(status)) = 'resolved'")
    cursor.execute("UPDATE complaints SET status = 'closed' WHERE LOWER(TRIM(status)) = 'closed'")
    cursor.execute(
        "UPDATE complaints SET status = 'pending' "
        "WHERE LOWER(TRIM(status)) NOT IN ('pending', 'under review', 'resolved', 'closed')"
    )
    cursor.execute(
        "UPDATE complaints "
        "SET ref = CONCAT('CM_', UPPER(LPAD(HEX(id), 8, '0'))) "
        "WHERE ref IS NULL OR TRIM(ref) = ''"
    )
    cursor.execute("ALTER TABLE complaints MODIFY ref VARCHAR(32) NOT NULL")
    cursor.execute("SHOW INDEX FROM complaints WHERE Column_name = 'ref' AND Non_unique = 0")
    has_unique_ref = cursor.fetchone() is not None
    if not has_unique_ref:
        cursor.execute("ALTER TABLE complaints ADD UNIQUE KEY uq_complaints_ref (ref)")

def setup_database():
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD
        )

        cursor = mydb.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS complaints ("
            "id INT AUTO_INCREMENT PRIMARY KEY,"
            "ref VARCHAR(32) NOT NULL UNIQUE,"
            "name VARCHAR(255) NOT NULL,"
            "email VARCHAR(255) NOT NULL,"
            "category VARCHAR(100) NOT NULL DEFAULT 'General feedback',"
            "urgency ENUM('low','medium','high') NOT NULL DEFAULT 'low',"
            "message TEXT NOT NULL,"
            "status VARCHAR(20) NOT NULL DEFAULT 'pending',"
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        ensure_schema(cursor)
        mydb.commit()
        print("congrats! Database setup done.")
        cursor.close()
        mydb.close()
    except Exception as e:
        print(f"Unable to set up database: {e}")

def connect_db():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            database=DB_NAME
        )
        return connection
    except Exception as e:
        print (f"There's an error while connecting to database: {e}")
        return None

if __name__ == "__main__":
    setup_database()
