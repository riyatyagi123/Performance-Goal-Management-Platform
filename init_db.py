import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# ================= USERS =================
cur.execute("DROP TABLE IF EXISTS users")
cur.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT,
    role TEXT,
    doj TEXT,
    review_track TEXT DEFAULT 'bi-annual'
)
""")

# ================= GOALS =================
cur.execute("DROP TABLE IF EXISTS goals")
cur.execute("""
CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_code TEXT,
    title TEXT,
    description TEXT,
    employee_id INTEGER,
    status TEXT,
    weightage INTEGER,
    progress INTEGER DEFAULT 0,
    submitted_at TEXT,
    parent_goal_id INTEGER,
    goal_level TEXT DEFAULT 'individual'
)
""")

# ================= GOAL FEEDBACK =================
cur.execute("DROP TABLE IF EXISTS feedback")
cur.execute("""
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    manager_id INTEGER,
    goal_id INTEGER,
    rating INTEGER,
    comment TEXT
)
""")

# ================= PROBATION =================
cur.execute("DROP TABLE IF EXISTS probation_reviews")
cur.execute("""
CREATE TABLE probation_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    stage INTEGER,
    self_feedback TEXT,
    manager_feedback TEXT,
    self_submitted INTEGER DEFAULT 0,
    manager_submitted INTEGER DEFAULT 0,
    created_at TEXT
)
""")

# ================= REVIEW CYCLES =================
cur.execute("DROP TABLE IF EXISTS review_cycles")
cur.execute("""
CREATE TABLE review_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    cycle_type TEXT,
    cycle_name TEXT,
    start_date TEXT,
    end_date TEXT,
    self_submitted INTEGER DEFAULT 0,
    manager_submitted INTEGER DEFAULT 0,
    self_feedback TEXT,
    manager_feedback TEXT,
    created_at TEXT
)
""")

# ================= UNIFIED FEEDBACK =================
cur.execute("DROP TABLE IF EXISTS feedback_responses")
cur.execute("""
CREATE TABLE feedback_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role TEXT,
    type TEXT,                    -- goal / probation / cycle
    reference_id INTEGER,         -- links to original table
    responses TEXT,               -- JSON
    rating INTEGER,
    sentiment TEXT,
    flagged INTEGER DEFAULT 0,
    flag_reason TEXT,
    flag_status TEXT DEFAULT 'pending',
    flag_action TEXT,
    created_at TEXT,
    goal_id INTEGER               -- 🔥 NEW: link to goal
)
""")

# ================= CONFIG =================
cur.execute("DROP TABLE IF EXISTS config")
cur.execute("""
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

# ================= EMAIL LOGS =================
cur.execute("DROP TABLE IF EXISTS email_logs")
cur.execute("""
CREATE TABLE email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id INTEGER,
    recipient_email TEXT,
    type TEXT,
    subject TEXT,
    status TEXT DEFAULT 'sent',
    sent_at TEXT
)
""")

# Default flag threshold
cur.execute("""
INSERT INTO config (key, value)
VALUES ('flag_threshold', '2')
""")

# ================= SAMPLE USERS =================
cur.executemany("""
INSERT INTO users (name, email, password, role, doj)
VALUES (?, ?, ?, ?, ?)
""", [
    ('Employee1', 'rogerrene1997@gmail.com', '123', 'employee', '2026-02-25'),
    ('Riya', 'riya@example.com', '123', 'employee', '2026-03-01'),
    ('Dipali', 'dipali@example.com', '123', 'employee', '2026-04-01'),
    ('Manager1', 'mgr@gmail.com', '123', 'manager', '2026-01-01'),
    ('Manager2', 'mgr2@example.com', '123', 'manager', '2026-01-15'),
    ('Admin1', 'admin@gmail.com', '123', 'admin', '2026-01-01')
])

conn.commit()
conn.close()

print("FINAL DATABASE READY WITH FEEDBACK MODULE")