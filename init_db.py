import sqlite3

DB_FILE = "library.db"

schema = """
CREATE TABLE IF NOT EXISTS shelves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shelf_id TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS racks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rack_id TEXT NOT NULL,
    shelf_id INTEGER,
    FOREIGN KEY (shelf_id) REFERENCES shelves (id)
);

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    author TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    rack_id INTEGER,
    FOREIGN KEY (rack_id) REFERENCES racks (id)
);

CREATE TABLE IF NOT EXISTS borrow_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    student_class TEXT NOT NULL,
    student_year TEXT NOT NULL,
    student_mobile TEXT NOT NULL,
    book_id INTEGER,
    borrow_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    reissued INTEGER DEFAULT 0,
    FOREIGN KEY (book_id) REFERENCES books (id)
);
"""

def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()
    conn.close()
    print("Database tables created successfully.")

if __name__ == "__main__":
    initialize_database()
