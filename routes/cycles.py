from flask import Blueprint, request, redirect, session
import json
from database import get_db
from utils import store_feedback

cycles_bp = Blueprint('cycles', __name__)

@cycles_bp.route('/submit_cycle_self/<int:id>', methods=['POST'])
def submit_cycle_self(id):
    data = dict(request.form)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE review_cycles SET self_feedback=?, self_submitted=1 WHERE id=?",
                (json.dumps(data), id))

    conn.commit()
    conn.close()

    store_feedback(session['user_id'], "employee", "cycle", id, data, None)

    return redirect('/employee')

@cycles_bp.route('/submit_cycle_manager/<int:id>', methods=['POST'])
def submit_cycle_manager(id):
    data = dict(request.form)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE review_cycles SET manager_feedback=?, manager_submitted=1 WHERE id=?",
                (json.dumps(data), id))

    conn.commit()
    conn.close()

    store_feedback(session['user_id'], "manager", "cycle", id, data, None)

    return redirect('/manager')
