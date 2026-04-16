from flask import Blueprint, render_template, request, redirect, session, Response
import json
import csv
from io import StringIO
from datetime import datetime
from database import get_db
from utils import calculate_performance_score, calculate_success_metrics, get_escalations
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin():
    conn = get_db()
    cur = conn.cursor()
    
    uid = session.get('user_id')
    cur.execute("SELECT * FROM email_logs WHERE recipient_id=? ORDER BY sent_at DESC LIMIT 3", (uid,))
    notifications = cur.fetchall()

    cur.execute("SELECT goals.*, users.name FROM goals JOIN users ON goals.employee_id = users.id")
    goals = cur.fetchall()

    cur.execute("SELECT probation_reviews.*, users.name FROM probation_reviews JOIN users ON probation_reviews.employee_id = users.id")
    raw_probation = cur.fetchall()

    probation = []

    for p in raw_probation:
     p = list(p)

    # Parse employee JSON
     try:
        p[3] = json.loads(p[3]) if p[3] else {}
     except:
        p[3] = {}

    # Parse manager JSON
     try:
        p[4] = json.loads(p[4]) if p[4] else {}
     except:
        p[4] = {}

     probation.append(p)

    cur.execute("SELECT review_cycles.*, users.name FROM review_cycles JOIN users ON review_cycles.employee_id = users.id")
    raw_cycles = cur.fetchall()
    cycles = []
    for c in raw_cycles:
        c_list = list(c)
        try:
            c_list[8] = json.loads(c_list[8]) if c_list[8] else {}
        except:
            c_list[8] = {}
        try:
            c_list[9] = json.loads(c_list[9]) if c_list[9] else {}
        except:
            c_list[9] = {}
        cycles.append(c_list)

    cur.execute("SELECT id, name FROM users WHERE role='employee'")
    employees = cur.fetchall()

    performance_data = []

    for e in employees:
     perf = calculate_performance_score(e[0])
     performance_data.append((e[1], perf))

    cur.execute("""
    SELECT feedback_responses.*, users.name, goals.title
    FROM feedback_responses
    JOIN users ON feedback_responses.user_id = users.id
    LEFT JOIN goals ON feedback_responses.goal_id = goals.id
    WHERE flagged=1
    """)
    flags = cur.fetchall()
    flag_with_age = []

    for f in flags:
     created = datetime.fromisoformat(f[12])
     age = (datetime.now() - created).days
     flag_with_age.append((f, age))

    # Escalation
    escalated_flags = []
    for f in flags:
     created = datetime.fromisoformat(f[12])

     if f[9] == 'pending' and (datetime.now() - created).days >= 7:
        escalated_flags.append(f)

        cur.execute("""
        UPDATE feedback_responses
        SET flag_status='escalated'
        WHERE id=?
        """, (f[0],))

    conn.commit()

    # Repeat flags
    repeat_flags = []

    cur.execute("""
      SELECT * FROM feedback_responses
      WHERE flagged=1
      ORDER BY user_id
      """)
    all_flags = cur.fetchall()

    user_map = {}
    for f in all_flags:
     uid = f[1]
     user_map.setdefault(uid, []).append(f)

    for uid, items in user_map.items():
     if len(items) >= 2:
        repeat_flags.append((uid, items))

    conn.close()

    success_metrics = calculate_success_metrics()

    return render_template("admin.html",
    goals=goals,
    probation_reviews=probation,
    cycles=cycles,
    flags=flag_with_age,
    escalated_flags=escalated_flags,
    repeat_flags=repeat_flags,
    performance_data=performance_data,
    success_metrics=success_metrics,
    escalations=get_escalations('admin'),
    notifications=notifications
    )


@admin_bp.route('/update_flag/<int:id>', methods=['POST'])
def update_flag(id):
    if session.get('role') != 'admin':
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE feedback_responses
    SET flag_status='resolved', flag_action=?
    WHERE id=?
    """, (request.form['action'], id))

    conn.commit()
    conn.close()

    return redirect('/admin')

@admin_bp.route('/export_goals')
def export_goals():
    if session.get('role') != 'admin':
        return "Unauthorized"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT goals.*, users.name FROM goals JOIN users ON goals.employee_id = users.id")
    goals = cur.fetchall()
    conn.close()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Goal ID', 'Title', 'Description', 'Employee', 'Status', 'Weightage', 'Progress'])
    for g in goals:
        cw.writerow([g[0], g[1], g[2], g[9], g[5], g[6], g[7]])
    
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=goals_export.csv"})

@admin_bp.route('/admin/users')
def manage_users():
    if session.get('role') != 'admin':
        return redirect('/login')
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role, doj, review_track FROM users ORDER BY id DESC")
    users = cur.fetchall()
    conn.close()
    
    return render_template('admin_users.html', users=users)

@admin_bp.route('/admin/users/add', methods=['POST'])
def add_user():
    if session.get('role') != 'admin':
        return redirect('/login')
        
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    doj = request.form.get('doj')
    review_track = request.form.get('review_track', 'bi-annual')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email, password, role, doj, review_track) VALUES (?, ?, ?, ?, ?, ?)",
        (name, email, password, role, doj, review_track)
    )
    conn.commit()
    conn.close()
    
    return redirect('/admin/users')

@admin_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect('/login')
        
    conn = get_db()
    cur = conn.cursor()
    
    # Cascade delete Everything
    # Goals
    cur.execute("DELETE FROM goals WHERE employee_id=?", (user_id,))
    # Feedback (where user is either employee or manager)
    cur.execute("DELETE FROM feedback WHERE employee_id=? OR manager_id=?", (user_id, user_id))
    # Probation Reviews
    cur.execute("DELETE FROM probation_reviews WHERE employee_id=?", (user_id,))
    # Review Cycles
    cur.execute("DELETE FROM review_cycles WHERE employee_id=?", (user_id,))
    # Feedback Responses (from surveys)
    cur.execute("DELETE FROM feedback_responses WHERE user_id=?", (user_id,))
    # Email Logs
    cur.execute("DELETE FROM email_logs WHERE recipient_id=?", (user_id,))
    
    # Finally, delete the user
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    
    conn.commit()
    conn.close()
    
    return redirect('/admin/users')

