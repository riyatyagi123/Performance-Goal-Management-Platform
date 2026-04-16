from flask import Blueprint, request, redirect, session
import json
from database import get_db
from utils import store_feedback

probation_bp = Blueprint('probation', __name__)

@probation_bp.route('/submit_self_review/<int:id>', methods=['POST'])
def submit_self_review(id):
    data = dict(request.form)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE probation_reviews SET self_feedback=?, self_submitted=1 WHERE id=?",
                (json.dumps(data), id))

    conn.commit()
    conn.close()

    store_feedback(session['user_id'], "employee", "probation", id, data, None)

    return redirect('/employee')

@probation_bp.route('/submit_manager_review/<int:id>', methods=['POST'])
def submit_manager_review(id):
    data = dict(request.form)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE probation_reviews SET manager_feedback=?, manager_submitted=1 WHERE id=?",
                (json.dumps(data), id))

    conn.commit()
    conn.close()

    store_feedback(session['user_id'], "manager", "probation", id, data, None)

    return redirect('/manager')
