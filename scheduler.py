import time
from datetime import datetime
from database import get_db
from utils import get_working_days
from threading import Thread

import smtplib
from email.message import EmailMessage

# ================= EMAIL CONFIG =================
# ACTION REQUIRED: Fill these in with your real Gmail and App Password
SMTP_EMAIL = "rogerrene1997@gmail.com"
SMTP_PASSWORD = "mvoiifjwazugpvet"
# ================================================

def send_real_email(to_email, subject, body):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return False
        
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_EMAIL
    msg['To'] = to_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False

def log_email(recipient_id, recipient_email, type_, subject, custom_body=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO email_logs (recipient_id, recipient_email, type, subject, status, sent_at)
        VALUES (?, ?, ?, ?, 'sent', ?)
    """, (recipient_id, recipient_email, type_, subject, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    body = custom_body if custom_body else f"Hello,\n\nThis is an automated alert regarding your PMS Profile: {subject}\n\nPlease login to the platform dashboard to view further details."
    
    # Fire the real email over the internet!
    send_real_email(recipient_email, subject, body)

def check_probation_triggers():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT id, name, email, doj FROM users WHERE role='employee'")
    employees = cur.fetchall()
    
    today_str = datetime.today().isoformat()
    
    for emp in employees:
        uid, name, email, doj = emp
        working_days = get_working_days(doj, today_str)
        
        for stage in [30, 60, 80]:
            if working_days >= stage:
                # Check if review was created for this stage
                # (employee dashboard actually creates it right now, but for testing if they haven't logged in, automation should create it too ideally.
                # Since PRD says "Automated triggers go out", let's make sure it's created if missing!)
                cur.execute("SELECT id, self_submitted, manager_submitted FROM probation_reviews WHERE employee_id=? AND stage=?", (uid, stage))
                review = cur.fetchone()
                
                if not review:
                    # Auto generate
                    cur.execute("""
                    INSERT INTO probation_reviews (employee_id, stage, created_at)
                    VALUES (?, ?, ?)
                    """, (uid, stage, today_str))
                    conn.commit()
                    self_sub, mgr_sub = 0, 0
                else:
                    _, self_sub, mgr_sub = review

                days_over = working_days - stage
                
                # Check if sent today to prevent spam loop if checking frequently
                cur.execute("SELECT id FROM email_logs WHERE recipient_id=? AND type='probation' AND subject LIKE ?", (uid, f"%{stage}%"))
                sent_trigger = cur.fetchone()
                
                if days_over == 0 and not sent_trigger:
                    # Send Employee form
                    emp_body = f"Hello {name},\n\nYour Probation Review ({stage} Days) is now due.\nPlease log in and complete your self-feedback form here: http://localhost:5000/employee\n\nThank you,\nHR"
                    log_email(uid, email, "probation", f"Probation Review ({stage} Days) is due", emp_body)
                    
                    # Send Manager form
                    cur.execute("SELECT id, email FROM users WHERE role='manager' LIMIT 1")
                    mgr = cur.fetchone()
                    if mgr:
                        mgr_body = f"Hello Manager,\n\nThe {stage}-Day Probation Review for {name} is now due.\nPlease complete the manager evaluation form here: http://localhost:5000/manager\n\nThank you,\nHR"
                        log_email(mgr[0], mgr[1], "probation", f"Manager Action Required: Probation Review for {name} ({stage} Days)", mgr_body)

                elif days_over in [2, 4, 6] and (self_sub == 0 or mgr_sub == 0):
                    # For reminder, see if sent today 
                    cur.execute("SELECT id FROM email_logs WHERE recipient_id=? AND type='reminder' AND subject LIKE ? AND date(sent_at) = date(?)", (uid, f"%{stage}%", today_str))
                    if not cur.fetchone():
                        if self_sub == 0:
                            emp_body = f"Hello {name},\n\nREMINDER: Your {stage}-Day Probation Review is pending.\nPlease log in and fill out the form here: http://localhost:5000/employee\n\nThank you,\nHR"
                            log_email(uid, email, "reminder", f"REMINDER: Probation Review ({stage} Days) pending", emp_body)
                        
                        if mgr_sub == 0:
                            cur.execute("SELECT id, email FROM users WHERE role='manager' LIMIT 1")
                            mgr = cur.fetchone()
                            if mgr:
                                cur.execute("SELECT id FROM email_logs WHERE recipient_id=? AND type='reminder' AND subject LIKE ? AND date(sent_at) = date(?)", (mgr[0], f"%{name}%{stage}%", today_str))
                                if not cur.fetchone():
                                    mgr_body = f"Hello Manager,\n\nREMINDER: The {stage}-Day Probation Review for {name} is pending.\nPlease log in and fill out the form here: http://localhost:5000/manager\n\nThank you,\nHR"
                                    log_email(mgr[0], mgr[1], "reminder", f"REMINDER: Probation for {name} ({stage} Days)", mgr_body)

                elif days_over >= 7 and (self_sub == 0 or mgr_sub == 0):
                    cur.execute("SELECT id, email FROM users WHERE role='admin' LIMIT 1")
                    admin = cur.fetchone()
                    if admin:
                         cur.execute("SELECT id FROM email_logs WHERE recipient_id=? AND type='escalation' AND subject LIKE ? AND date(sent_at) = date(?)", (admin[0], f"%{name}%{stage}%", today_str))
                         if not cur.fetchone():
                             admin_body = f"Hello Admin,\n\nESCALATION: {name}'s {stage}-Day Probation Review is {days_over} days overdue.\nPlease access the Admin Dashboard to take action: http://localhost:5000/admin\n\nSystem"
                             log_email(admin[0], admin[1], "escalation", f"ESCALATION: {name}'s {stage}-Day Probation Review is {days_over} days overdue", admin_body)
                            
    conn.close()

def check_review_cycle_triggers():
    from utils import get_current_cycle_details
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT id, name, email, review_track FROM users WHERE role='employee'")
    employees = cur.fetchall()
    
    today = datetime.today()
    today_str = today.isoformat()
    
    cur.execute("SELECT id, email FROM users WHERE role='admin' LIMIT 1")
    admin = cur.fetchone()
    
    for emp in employees:
        uid, name, email, review_track = emp
        if not review_track: review_track = 'bi-annual'
        
        cycle_name, start, end, t_month, t_year = get_current_cycle_details(review_track, today)
        
        if today.month == t_month and today.year == t_year:
            cur.execute("SELECT * FROM review_cycles WHERE employee_id=? AND cycle_name=? AND start_date=?", (uid, cycle_name, start))
            review = cur.fetchone()
            
            if review:
                self_sub, mgr_sub = review[6], review[7]
                
                def email_not_sent(subject_like):
                    cur.execute("SELECT id FROM email_logs WHERE recipient_id=? AND type='review_cycle' AND subject LIKE ? AND date(sent_at) = date(?)", (uid, subject_like, today_str))
                    return not cur.fetchone()
                
                if today.day == 1 and email_not_sent("%is due%"):
                    log_email(uid, email, "review_cycle", f"{cycle_name} Performance Review is due")
                
                elif today.day == 5 and (self_sub == 0 or mgr_sub == 0) and email_not_sent("%Gentle Reminder%"):
                    log_email(uid, email, "review_cycle", f"Gentle Reminder: {cycle_name} Review pending")
                
                elif today.day == 15 and (self_sub == 0 or mgr_sub == 0) and email_not_sent("%Urgent Reminder%"):
                    log_email(uid, email, "review_cycle", f"Urgent Reminder: {cycle_name} Review pending")
                
                elif today.day == 22 and (self_sub == 0 or mgr_sub == 0):
                    if admin:
                        cur.execute("SELECT id FROM email_logs WHERE recipient_id=? AND type='escalation' AND subject LIKE ? AND date(sent_at) = date(?)", (admin[0], f"%{name} {cycle_name}%", today_str))
                        if not cur.fetchone():
                             log_email(admin[0], admin[1], "escalation", f"ESCALATION: {name} {cycle_name} Review is pending escalation")
                             
    conn.close()

def run_scheduler_loop():
    print("🚀 Automation Engine Started...")
    while True:
        try:
            check_probation_triggers()
            check_review_cycle_triggers()
        except Exception as e:
            print(f"Scheduler error: {e}")
        time.sleep(3600)  # Check every hour

def start_scheduler():
    t = Thread(target=run_scheduler_loop, daemon=True)
    t.start()
