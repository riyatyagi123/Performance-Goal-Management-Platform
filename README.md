# 🚀 Enterprise Performance Management System (PMS)

Welcome to the **Performance Management System (PMS)** — a centralized, role-based web application built to streamline goal tracking, probation monitoring, and employee performance reviews.

---

## 🌐 Live Demo

The application is deployed on Render:

**🔗 Live URL:** https://pms-system1.onrender.com

---

## 🚀 Overview

The PMS platform is designed to replace fragmented spreadsheets and informal email threads with automated workflows and real-time dashboards. It serves three distinct roles with tailored experiences:

* **Employees**: Set goals, submit self-assessments, and track their probation timelines.
* **Managers**: Assign goals, review team performance, approve pending tasks, and provide structured feedback.
* **Administrators**: Oversee the entire organization, manage the user repository ("People Management"), track aggregate performance scores, and handle system escalations.

---

## 🛠️ Technology Stack

* **Backend**: Python, Flask
* **Database**: SQLite (`database.db`)
* **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3
* **Icons & UI**: FontAwesome 6, Glassmorphic / Premium SaaS Design framework

---

## ✨ Key Features

1. **Role-based Authentication**: Secure, distinct dashboards for Employees, Managers, and Admins.
2. **Goal Management System (GMS)**: Assign, track, and update dynamic goals with weightage-based progression.
3. **Automated Review Cycles**: Dedicated tracking for Bi-Annual and Quarterly performance review tracks.
4. **Probation Monitoring**: 30/60/80-day automated staggered checkpoint reviews for new hires.
5. **Real-time Email Emulation**: Background jobs and dynamic scheduler simulating automated email notifications right on the dashboard.
6. **Escalation Center**: Admins can flag toxic/unprofessional feedback and gracefully escalate delayed manager responses.
7. **Premium "People Management" Module**: Instantly Add/Remove users with cascading data deletion ensuring database integrity.

---

## 📁 Project Structure

```
Opstree1/
│
├── app.py                  # Main Flask application initialization and configuration
├── database.py             # Database connection wrapper and queries
├── init_db.py              # Schema definition and database seeding script
├── scheduler.py            # Background operations (email automation/escalation triggers)
├── utils.py                # Helper functions for calculation and data processing
│
├── routes/                 # Separated route blueprints for modularity
│   ├── auth.py             # Login, Logout logic
│   ├── employee.py         # Employee dashboard actions
│   ├── manager.py          # Manager dashboard logic
│   └── admin.py            # Admin logic & People Management
│
├── templates/              # HTML standard templates (Jinja2)
│   ├── login.html
│   ├── employee.html
│   ├── manager.html
│   ├── admin.html
│   └── admin_users.html    # People Management Grid 
│
└── static/                 # CSS/JS and Images
    └── custom.css          # Core SaaS Aesthetic Style Overrides
```

---

## ⚙️ How to Setup and Run

1. **Prerequisites**
   Ensure you have Python 3.x installed.

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the Database**

   ```bash
   python init_db.py
   ```

   *Note: This will recreate tables with sample users.*

4. **Run the Application**

   ```bash
   python app.py
   ```

   The server will start on `http://127.0.0.1:5000`.

5. **Run the Scheduler (Optional)**

   ```bash
   python scheduler.py
   ```

---

## 🔐 Demo Credentials

* **Admin**: [admin@gmail.com](mailto:admin@gmail.com)
* **Manager**: [mgr@gmail.com](mailto:mgr@gmail.com)
* **Employee**: [riya@example.com](mailto:riya@example.com)
* **Password (all users)**: 123

---

## 🎨 Design Philosophy

The system prioritizes a **Premium SaaS aesthetic**:

* Fully responsive Bootstrap grids
* Clean UI with soft shadows and whitespace
* Structured navigation with a modern dashboard layout
* Consistent color scheme for actions and alerts

---

## ⚠️ Notes

* SQLite is used for demonstration purposes
* On Render free tier, database resets on redeploy
* For production, PostgreSQL is recommended

---

*Built for modern workforce management.*
