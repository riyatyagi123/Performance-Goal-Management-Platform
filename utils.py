import json
from datetime import datetime, timedelta
from database import get_db

def detect_flag(data, rating):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT value FROM config WHERE key='flag_threshold'")
    row = cur.fetchone()
    if not row:
     return 0, "Threshold not configured"

    threshold = int(row[0])

    reasons = []

    if rating is not None and rating <= threshold:
        reasons.append("Low Rating")

    negative_words = ["bad", "poor", "stress", "issue", "problem"]

    for v in data.values():
        if isinstance(v, str):
            if any(word in v.lower() for word in negative_words):
                reasons.append("Negative Sentiment")

            if v.strip() == "":
                reasons.append("Incomplete Response")

    flagged = 1 if reasons else 0
    return flagged, ", ".join(set(reasons))

def store_feedback(user_id, role, type_, ref_id, data, rating):
    flagged, reason = detect_flag(data, rating)

    goal_id = None
    if type_ == "goal":
        goal_id = ref_id

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO feedback_responses
    (user_id, role, type, reference_id, responses, rating, sentiment,
     flagged, flag_reason, flag_status, flag_action, created_at, goal_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, role, type_, ref_id,
        json.dumps(data),
        rating,
        "negative" if flagged else "positive",
        flagged,
        reason,
        "pending",
        None,
        datetime.now().isoformat(),
        goal_id
    ))

    conn.commit()
    conn.close()

def calculate_goal_score(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT progress, weightage
    FROM goals
    WHERE employee_id=? AND status IN ('Active','Completed','Archived')
    """, (user_id,))

    goals = cur.fetchall()
    conn.close()

    if not goals:
        return 0

    total = 0
    for g in goals:
        progress = g[0]
        weight = g[1]
        total += (progress * weight) / 100

    return round(total, 2)

def calculate_rating_score(user_id):
    conn = get_db()
    cur = conn.cursor()

    # 1. Goal feedback ratings
    cur.execute("""
    SELECT rating FROM feedback
    WHERE employee_id=?
    """, (user_id,))

    goal_ratings = [r[0] for r in cur.fetchall()]

    # 2. Cycle feedback ratings
    cur.execute("SELECT manager_feedback FROM review_cycles WHERE employee_id=? AND manager_submitted=1", (user_id,))
    cycle_feedbacks = cur.fetchall()
    
    conn.close()

    cycle_ratings = []
    for cf in cycle_feedbacks:
        if cf[0]:
            try:
                data = json.loads(cf[0])
                r_text = data.get("rating", "")
                if r_text == "Above Expectations":
                    cycle_ratings.append(5)
                elif r_text == "Meets Expectations":
                    cycle_ratings.append(3)
                elif r_text == "Below Expectations":
                    cycle_ratings.append(1)
            except:
                pass

    all_ratings = goal_ratings + cycle_ratings

    if not all_ratings:
        return 0

    avg = sum(all_ratings) / len(all_ratings)
    return round((avg / 5) * 100, 2)

def calculate_behavior_score(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*) FROM feedback_responses
    WHERE user_id=? AND flagged=1
    """, (user_id,))

    count = cur.fetchone()[0]
    conn.close()

    if count == 0:
        return 100
    elif count == 1:
        return 70
    else:
        return 40

def calculate_performance_score(user_id):
    goal = calculate_goal_score(user_id)
    rating = calculate_rating_score(user_id)
    behavior = calculate_behavior_score(user_id)

    score = (goal * 0.5) + (rating * 0.3) + (behavior * 0.2)

    return {
        "goal": goal,
        "rating": rating,
        "behavior": behavior,
        "final": round(score, 2)
    }

def get_working_days(start_date_str, end_date_str=None):
    if not start_date_str: return 0
    start = datetime.fromisoformat(start_date_str) if 'T' in start_date_str else datetime.strptime(start_date_str, "%Y-%m-%d")
    
    if end_date_str:
        end = datetime.fromisoformat(end_date_str) if 'T' in end_date_str else datetime.strptime(end_date_str, "%Y-%m-%d")
    else:
        end = datetime.today()
    
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5: # Monday to Friday
            days += 1
        current += timedelta(days=1)
    return days

def calculate_success_metrics():
    conn = get_db()
    cur = conn.cursor()

    metrics = {
        "emails_sent": 0,
        "form_completion_rate": 0,
        "flag_turnaround_days": 2.5 # Mock SLA
    }

    cur.execute("SELECT COUNT(*) FROM email_logs WHERE status='sent'")
    metrics["emails_sent"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM probation_reviews")
    total_reviews = cur.fetchone()[0] * 2

    cur.execute("SELECT SUM(self_submitted + manager_submitted) FROM probation_reviews")
    completed = cur.fetchone()[0] or 0

    if total_reviews > 0:
        metrics["form_completion_rate"] = round((completed / total_reviews) * 100, 1)

    conn.close()
    return metrics


def get_escalations(role, user_id=None):
    from database import get_db
    conn = get_db()
    cur = conn.cursor()
    escalations = []
    today = datetime.today()
    today_str = today.isoformat()

    cur.execute("SELECT g.id, g.title, g.submitted_at, u.name, u.id FROM goals g JOIN users u ON g.employee_id = u.id WHERE g.status='Pending Approval'")
    goals = cur.fetchall()
    for g in goals:
        if g[2]:
            delay = get_working_days(g[2], today_str)
            if delay >= 5:
                escalations.append({
                    "type": "Goal Approval",
                    "employee_name": g[3],
                    "employee_id": g[4],
                    "description": f"Goal '{g[1]}' pending approval for {delay} days.",
                    "action": "Needs Approval",
                    "severity": "danger" if delay >= 10 else "warning"
                })

    cur.execute("SELECT p.id, p.stage, p.self_submitted, p.manager_submitted, u.name, u.doj, u.id FROM probation_reviews p JOIN users u ON p.employee_id = u.id")
    probations = cur.fetchall()
    for p in probations:
        stage = p[1]
        self_sub, mgr_sub = p[2], p[3]
        if self_sub == 0 or mgr_sub == 0:
            wd = get_working_days(p[5], today_str)
            days_over = wd - stage
            if days_over >= 7:
                escalations.append({
                    "type": "Probation Review",
                    "employee_name": p[4],
                    "employee_id": p[6],
                    "description": f"{stage}-Day Review is {days_over} days overdue.",
                    "action": "Missing Feedback",
                    "severity": "danger"
                })

    cur.execute("SELECT c.id, c.cycle_name, c.self_submitted, c.manager_submitted, c.created_at, u.name, u.id, u.review_track FROM review_cycles c JOIN users u ON c.employee_id = u.id")
    cycles = cur.fetchall()
    for c in cycles:
        if c[2] == 0 or c[3] == 0:
            track = c[7] if c[7] else 'bi-annual'
            _, _, _, t_month, t_year = get_current_cycle_details(track, today)
            
            if today.year == t_year and today.month == t_month and today.day >= 22:
                escalations.append({
                    "type": "Review Cycle",
                    "employee_name": c[5],
                    "employee_id": c[6],
                    "description": f"{c[1]} Cycle pending past 22nd deadline.",
                    "action": "Urgent Form Completion",
                    "severity": "danger"
                })

    if role == 'admin':
        cur.execute("SELECT f.id, f.type, f.flag_reason, f.created_at, u.name, u.id FROM feedback_responses f JOIN users u ON f.user_id = u.id WHERE f.flag_status='pending'")
        flags = cur.fetchall()
        for f in flags:
            created = datetime.fromisoformat(f[3])
            age = (today - created).days
            if age >= 7:
                 escalations.append({
                    "type": "Unresolved Flag",
                    "employee_name": f[4],
                    "employee_id": f[5],
                    "description": f"Flag pending for {age} days: {f[2]}",
                    "action": "Needs Admin Resolution",
                    "severity": "danger"
                })
    conn.close()

    if role == 'employee' and user_id:
        escalations = [e for e in escalations if e["employee_id"] == user_id]

    return escalations

def get_current_cycle_details(track, today=None):
    if not today:
        from datetime import datetime
        today = datetime.today()
    year = today.year
    month = today.month

    if track == 'quarterly':
        if month <= 3:
            return "Q1", f"{year}-01-01", f"{year}-03-31", 4, year
        elif month <= 6:
            return "Q2", f"{year}-04-01", f"{year}-06-30", 7, year
        elif month <= 9:
            return "Q3", f"{year}-07-01", f"{year}-09-30", 10, year
        else:
            return "Q4", f"{year}-10-01", f"{year}-12-31", 1, year + 1
    else:
        if 4 <= month <= 9:
            return "Cycle 1", f"{year}-04-01", f"{year}-09-30", 8, year
        else:
            if month < 4:
                return "Cycle 2", f"{year-1}-10-01", f"{year}-03-31", 2, year
            else:
                return "Cycle 2", f"{year}-10-01", f"{year+1}-03-31", 2, year + 1
