from flask import Blueprint, request, redirect, session
from datetime import datetime
from database import get_db

goals_bp = Blueprint('goals', __name__)

@goals_bp.route('/create_goal', methods=['POST'])
def create_goal():
    conn = get_db()
    cur = conn.cursor()

    weight = int(request.form['weightage'])

    cur.execute("""
    SELECT SUM(weightage) FROM goals
    WHERE employee_id=? AND status IN ('Draft','Active','Pending Approval')
    """, (session['user_id'],))

    total = cur.fetchone()[0] or 0

    if total + weight > 100:
        return "Weightage exceeded"

    code = f"PMS-{cur.execute('SELECT COUNT(*) FROM goals').fetchone()[0] + 1:03d}"

    cur.execute("""
    INSERT INTO goals (goal_code, title, description, employee_id, status, weightage, progress)
    VALUES (?, ?, ?, ?, 'Draft', ?, 0)
    """, (code, request.form['title'], request.form['description'], session['user_id'], weight))

    conn.commit()
    conn.close()
    return redirect('/employee')

@goals_bp.route('/submit_goal/<int:id>')
def submit_goal(id):
    if session.get('role') != 'employee':
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE goals SET status='Pending Approval', submitted_at=?
    WHERE id=? AND employee_id=?
    """, (datetime.now().isoformat(), id, session['user_id']))

    conn.commit()
    conn.close()
    return redirect('/employee')

@goals_bp.route('/update_progress/<int:id>', methods=['POST'])
def update_progress(id):
    if session.get('role') != 'employee':
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE goals SET progress=?
    WHERE id=? AND status='Active' AND employee_id=?
    """, (int(request.form['progress']), id, session['user_id']))

    conn.commit()
    conn.close()
    return redirect('/employee')

@goals_bp.route('/complete_goal/<int:id>')
def complete_goal(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE goals SET status='Completed', progress=100 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/employee')

@goals_bp.route('/archive_goal/<int:id>')
def archive_goal(id):
    if session.get('role') != 'admin':
        return "Unauthorized"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE goals SET status='Archived' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')
