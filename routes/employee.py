from flask import Blueprint, render_template, session, Response
from datetime import datetime, timedelta

import json
from database import get_db
from utils import get_working_days, get_escalations, get_current_cycle_details

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/employee')
def employee():
    conn = get_db()
    cur = conn.cursor()

    uid = session['user_id']
    
    cur.execute("SELECT * FROM email_logs WHERE recipient_id=? ORDER BY sent_at DESC LIMIT 3", (uid,))
    notifications = cur.fetchall()

    cur.execute("SELECT * FROM goals WHERE employee_id=?", (uid,))
    goals = cur.fetchall()

    total_weight = sum([g[6] for g in goals if g[5] in ['Active', 'Pending Approval']])
    has_active_goals = any(g[5] == 'Active' for g in goals)

    cur.execute("SELECT * FROM feedback WHERE employee_id=?", (uid,))
    feedback = cur.fetchall()

    # Probation auto-create
    cur.execute("SELECT doj, review_track FROM users WHERE id=?", (uid,))
    row = cur.fetchone()
    doj_str = row[0]
    review_track = row[1] or 'bi-annual'

    today = datetime.today()
    today_str = today.isoformat()
    working_days = get_working_days(doj_str, today_str)

    for stage in [30, 60, 80]:
        if working_days >= stage:
            cur.execute("SELECT * FROM probation_reviews WHERE employee_id=? AND stage=?", (uid, stage))
            if not cur.fetchone():
                created_date = datetime.strptime(doj_str, "%Y-%m-%d") + timedelta(days=stage)
                cur.execute("""
                INSERT INTO probation_reviews (employee_id, stage, created_at)
                VALUES (?, ?, ?)
                """, (uid, stage, created_date.isoformat()))
                conn.commit()

    cur.execute("SELECT * FROM probation_reviews WHERE employee_id=?", (uid,))
    probation = cur.fetchall()

    probation_with_delay = []
    for p in probation:
      delay = (today - datetime.fromisoformat(p[7])).days
      parsed = list(p)

      # Cross-sharing logic: only show manager feedback if both have submitted
      both_submitted = (parsed[5] == 1 and parsed[6] == 1)

      parsed[3] = json.loads(p[3]) if p[3] else {}
      parsed[4] = json.loads(p[4]) if both_submitted and p[4] else {}
      
      # Inject flag so frontend knows it's waiting
      parsed.append(both_submitted)

      probation_with_delay.append((parsed, delay))
      
    # Review cycles auto-create based on track
    cycle_name, start, end, t_month, t_year = get_current_cycle_details(review_track, today)

    # Convert doj to datetime and end to datetime to enforce 60 day rule
    try:
        doj_date = datetime.fromisoformat(doj_str) if 'T' in doj_str else datetime.strptime(doj_str, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        
        # Mid-cycle joiners: eligibility cutoff = joined more than 60 days before cycle close.
        if (end_date - doj_date).days > 60:
            cur.execute("SELECT * FROM review_cycles WHERE employee_id=? AND cycle_name=? AND start_date=?", (uid, cycle_name, start))
            if not cur.fetchone():
                cur.execute("""
                INSERT INTO review_cycles
                (employee_id, cycle_type, cycle_name, start_date, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (uid, review_track, cycle_name, start, end, datetime.now().isoformat()))
                conn.commit()
    except Exception as e:
        print("Error checking eligibility for cycle auto-enroll:", e)

    cur.execute("SELECT * FROM review_cycles WHERE employee_id=?", (uid,))
    raw_cycles = cur.fetchall()
    
    cycles = []
    for c in raw_cycles:
        c_list = list(c)
        both_sub = (c_list[6] == 1 and c_list[7] == 1)
        if not both_sub:
            c_list[9] = None # Hide manager feedback
            
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

    conn.close()

    return render_template("employee.html",
        goals=goals,
        feedback=feedback,
        probation_with_delay=probation_with_delay,
        cycles=cycles,
        total_weight=total_weight,
        has_active_goals=has_active_goals,
        escalations=get_escalations('employee', uid),
        notifications=notifications
    )

@employee_bp.route('/export_my_goals')
def export_my_goals():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT goal_code, title, description, status, weightage, progress FROM goals WHERE employee_id=?", (session['user_id'],))
    goals = cur.fetchall()
    conn.close()

    def generate():
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Code', 'Title', 'Description', 'Status', 'Weightage', 'Progress'])
        for g in goals:
            writer.writerow([g[0], g[1], g[2], g[3], g[4], g[5]])
        return output.getvalue()

    return Response(generate(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=my_goals.csv"})
