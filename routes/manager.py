from flask import Blueprint, render_template, request, redirect, session
import json
from datetime import datetime
from database import get_db
from utils import store_feedback, get_escalations

manager_bp = Blueprint('manager', __name__)

@manager_bp.route('/manager')
def manager():
    conn = get_db()
    cur = conn.cursor()
    
    uid = session.get('user_id')
    cur.execute("SELECT * FROM email_logs WHERE recipient_id=? ORDER BY sent_at DESC LIMIT 3", (uid,))
    notifications = cur.fetchall()

    cur.execute("SELECT goals.*, users.name FROM goals JOIN users ON goals.employee_id = users.id WHERE status='Pending Approval'")
    pending_goals = cur.fetchall()

    cur.execute("SELECT goals.*, users.name FROM goals JOIN users ON goals.employee_id = users.id WHERE status='Active'")
    active_goals = cur.fetchall()

    cur.execute("SELECT * FROM feedback")
    feedback = cur.fetchall()

    cur.execute("SELECT probation_reviews.*, users.name FROM probation_reviews JOIN users ON probation_reviews.employee_id = users.id")
    probation_reviews = cur.fetchall()

    parsed_probation = []

    for p in probation_reviews:
     p = list(p)

     both_sub = (p[5] == 1 and p[6] == 1)

    # Parse employee JSON (hide if not both)
     p[3] = json.loads(p[3]) if both_sub and p[3] else {}
     p[4] = json.loads(p[4]) if p[4] else {}

     p.append(both_sub)
     parsed_probation.append(p)

    probation_reviews = parsed_probation

    cur.execute("SELECT review_cycles.*, users.name FROM review_cycles JOIN users ON review_cycles.employee_id = users.id")
    raw_cycles = cur.fetchall()

    cycles = []
    for c in raw_cycles:
        c_list = list(c)
        both_sub = (c_list[6] == 1 and c_list[7] == 1)
        if not both_sub:
            c_list[8] = None # Hide employee feedback
            
        try:
            c_list[8] = json.loads(c_list[8]) if c_list[8] else {}
        except:
            c_list[8] = {}
        try:
            c_list[9] = json.loads(c_list[9]) if c_list[9] else {}
        except:
            c_list[9] = {}
            
        c_list.append(both_sub)
        cycles.append(c_list)

    cur.execute("SELECT id, name FROM users WHERE role='employee'")
    team_employees = cur.fetchall()

    conn.close()

    return render_template("manager.html",
        pending_goals=pending_goals,
        active_goals=active_goals,
        feedback=feedback,
        probation_reviews=probation_reviews,
        cycles=cycles,
        team_employees=team_employees,
        escalations=get_escalations('manager'),
        notifications=notifications
    )

@manager_bp.route('/approve_goal/<int:id>')
def approve_goal(id):
    if session.get('role') not in ['manager', 'admin']:
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT employee_id, weightage, title FROM goals WHERE id=?", (id,))
    row = cur.fetchone()
    if not row:
        return redirect('/manager')
    emp_id, weight, title = row

    cur.execute("SELECT SUM(weightage) FROM goals WHERE employee_id=? AND status='Active'", (emp_id,))
    total = cur.fetchone()[0] or 0

    if total + weight > 100:
        return "Weightage exceeds"

    cur.execute("UPDATE goals SET status='Active' WHERE id=?", (id,))
    
    cur.execute("SELECT email FROM users WHERE id=?", (emp_id,))
    emp_email = cur.fetchone()[0]
    
    cur.execute("""
        INSERT INTO email_logs (recipient_id, recipient_email, type, subject, sent_at)
        VALUES (?, ?, 'goal_approved', ?, ?)
    """, (emp_id, emp_email, f"Goal Approved: {title}", datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return redirect('/manager')

@manager_bp.route('/reject_goal/<int:id>', methods=['POST'])
def reject_goal(id):
    if session.get('role') not in ['manager', 'admin']:
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE goals SET status='Draft' WHERE id=?", (id,))
    
    cur.execute("SELECT employee_id, title FROM goals WHERE id=?", (id,))
    emp_id, title = cur.fetchone()
    
    cur.execute("SELECT email FROM users WHERE id=?", (emp_id,))
    emp_email = cur.fetchone()[0]
    
    reason = request.form['reason']
    cur.execute("""
        INSERT INTO email_logs (recipient_id, recipient_email, type, subject, sent_at)
        VALUES (?, ?, 'goal_rejected', ?, ?)
    """, (emp_id, emp_email, f"Goal Rejected: {title} - {reason}", datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return redirect('/manager')

@manager_bp.route('/assign_goal', methods=['POST'])
def assign_goal():
    if session.get('role') not in ['manager', 'admin']:
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()

    emp_id = request.form['employee_id']
    title = request.form['title']
    desc = request.form['description']
    weight = int(request.form['weightage'])

    cur.execute("SELECT SUM(weightage) FROM goals WHERE employee_id=? AND status IN ('Active', 'Pending Approval')", (emp_id,))
    total = cur.fetchone()[0] or 0

    if total + weight > 100:
        return "Error: Cannot exceed 100% active weight."

    cur.execute("SELECT COUNT(*) FROM goals")
    count = cur.fetchone()[0] + 1
    goal_code = f"PMS-{count:03d}"

    cur.execute("""
    INSERT INTO goals (goal_code, title, description, employee_id, status, weightage, progress, submitted_at)
    VALUES (?, ?, ?, ?, 'Active', ?, 0, ?)
    """, (goal_code, title, desc, emp_id, weight, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return redirect('/manager')

@manager_bp.route('/manager_feedback/<int:goal_id>', methods=['POST'])
def manager_feedback(goal_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT employee_id FROM goals WHERE id=?", (goal_id,))
    emp = cur.fetchone()[0]

    rating = int(request.form['rating'])

    cur.execute("""
    INSERT INTO feedback (employee_id, manager_id, goal_id, rating, comment)
    VALUES (?, ?, ?, ?, ?)
    """, (emp, session['user_id'], goal_id, rating, request.form['comment']))

    conn.commit()
    conn.close()

    store_feedback(session['user_id'], "manager", "goal", goal_id,
                   {"comment": request.form['comment']}, rating)

    return redirect('/manager')

@manager_bp.route('/api/goal/<code>')
def api_goal(code):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT title, description FROM goals WHERE goal_code=?", (code,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"found": True, "title": row[0], "description": row[1]}
    return {"found": False}

