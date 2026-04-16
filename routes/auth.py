from flask import Blueprint, render_template, request, redirect, session
from database import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def login():
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def do_login():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=? AND password=?",
                (request.form['email'], request.form['password']))

    user = cur.fetchone()

    if user:
        session['user_id'] = user[0]
        session['role'] = user[4]
        return redirect(f"/{user[4]}")

    return "Invalid login"

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')
