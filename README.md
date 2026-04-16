# 🚀 Enterprise Performance Management System (PMS)

The **Performance Management System (PMS)** is a centralized, role-based web application designed to streamline employee goal tracking, probation monitoring, and performance evaluations within an organization.

---

## 🌐 Live Deployment

The application is deployed on Render:

**URL:** https://pms-system.onrender.com

---

## 📌 Overview

The PMS platform replaces manual processes such as spreadsheets and email-based tracking with an integrated system that provides structured workflows, real-time dashboards, and role-specific functionality.

### User Roles

* **Employee**

  * Define and manage individual goals
  * Submit self-assessments
  * Track probation progress

* **Manager**

  * Assign and evaluate goals
  * Review employee performance
  * Provide structured feedback

* **Administrator**

  * Manage users and organizational data
  * Monitor system-wide performance metrics
  * Handle escalations and moderation

---

## 🛠️ Technology Stack

* **Backend:** Python, Flask
* **Frontend:** HTML, CSS, JavaScript, Bootstrap
* **Database:** SQLite
* **Server:** Gunicorn
* **Deployment:** Render

---

## ✨ Key Features

* Role-based authentication and access control
* Goal Management System with weighted tracking
* Automated review cycles (quarterly and bi-annual)
* Probation monitoring with staged checkpoints (30/60/80 days)
* Scheduler-driven notification simulation
* Escalation system for delayed or inappropriate feedback
* Administrative “People Management” module

---

## 📁 Project Structure

```id="z1vlx1"
Opstree1/
│
├── app.py
├── database.py
├── init_db.py
├── scheduler.py
├── utils.py
│
├── routes/
│   ├── auth.py
│   ├── employee.py
│   ├── manager.py
│   └── admin.py
│
├── templates/
├── static/
├── requirements.txt
└── .gitignore
```

---

## ⚙️ Local Setup

### 1. Clone the Repository

```bash id="4mbf7g"
git clone https://github.com/riyatyagi123/Performance-Goal-Management-Platform.git
cd Performance-Goal-Management-Platform
```

### 2. Install Dependencies

```bash id="p1qnbh"
pip install -r requirements.txt
```

### 3. Initialize Database

```bash id="uv61pa"
python init_db.py
```

### 4. Run Application

```bash id="d4a8pt"
python app.py
```

Access the application at:
http://127.0.0.1:5000

---

## ☁️ Deployment Configuration

This application is configured for deployment on Render.

**Build Command**

```bash id="4qczlm"
pip install -r requirements.txt
```

**Start Command**

```bash id="q0n6k8"
python init_db.py && gunicorn app:app
```

---

## 🔐 Demo Credentials

| Role     | Email                                                     | Password |
| -------- | --------------------------------------------------------- | -------- |
| Admin    | [admin@gmail.com](mailto:admin@gmail.com)                 | 123      |
| Manager  | [mgr@gmail.com](mailto:mgr@gmail.com)                     | 123      |
| Employee | [rogerrene1997@gmail.com](mailto:rogerrene1997@gmail.com) | 123      |

---

## ⚠️ Notes

* The application uses SQLite for simplicity and demonstration purposes
* On Render’s free tier, the database is ephemeral and resets on redeploy
* For production use, a persistent database such as PostgreSQL is recommended

---

## 🚀 Future Enhancements

* Migration to PostgreSQL for persistent storage
* Integration of real email services (SMTP)
* Token-based authentication (JWT)
* Advanced analytics and reporting dashboards
* Modular microservices architecture

---

## 👩‍💻 Author

Riya Tyagi
B.Tech Computer Science Engineering

---

## 📄 License

This project is developed for academic and demonstration purposes.
