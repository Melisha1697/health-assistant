import sqlite3

def init_db():
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()

    # Add a default admin user
    try:
        c.execute('''
            INSERT INTO users (username, email, password, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@example.com', 'admin123', 1))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Admin user already exists

    conn.close()

if __name__ == "__main__":
    init_db()
