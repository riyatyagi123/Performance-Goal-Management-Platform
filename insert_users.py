import sqlite3

def add_users():
    db_path = "database.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    users = [
        ('Riya', 'riya@example.com', '123', 'employee', '2026-03-01', 'bi-annual'),
        ('Dipali', 'dipali@example.com', '123', 'employee', '2026-04-01', 'bi-annual'),
        ('Manager2', 'mgr2@example.com', '123', 'manager', '2026-01-15', 'bi-annual')
    ]
    
    try:
        for u in users:
            cur.execute("SELECT id FROM users WHERE email=?", (u[1],))
            if not cur.fetchone():
                cur.execute("INSERT INTO users (name, email, password, role, doj, review_track) VALUES (?, ?, ?, ?, ?, ?)", u)
        conn.commit()
        print("Users successfully added!")
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    add_users()
