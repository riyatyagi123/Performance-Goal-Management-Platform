from flask import Flask
from routes.auth import auth_bp
from routes.employee import employee_bp
from routes.goals import goals_bp
from routes.probation import probation_bp
from routes.cycles import cycles_bp
from routes.manager import manager_bp
from routes.admin import admin_bp
from scheduler import start_scheduler
import os

app = Flask(__name__)
app.secret_key = "secret"

app.register_blueprint(auth_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(probation_bp)
app.register_blueprint(cycles_bp)
app.register_blueprint(manager_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        start_scheduler()
    app.run(debug=True)