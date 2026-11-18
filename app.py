import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")
DATABASE = os.path.join(app.root_path, "complaints.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student'
    );
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        admin_reply TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    admin = db.execute("SELECT id FROM users WHERE email=?", ("admin@college.com",)).fetchone()
    if not admin:
        db.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                   ("College Admin", "admin@college.com", generate_password_hash("Admin@123"), "admin"))
    db.commit()
    db.close()

def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You do not have permission to view that page.", "danger")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        return wrapped
    return decorator

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter all details. Password must be at least 6 characters.", "danger")
            return render_template("register.html")
        try:
            db = get_db()
            db.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,'student')",
                       (name, email, generate_password_hash(password)))
            db.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "student_dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/student")
@login_required("student")
def student_dashboard():
    complaints = get_db().execute(
        "SELECT * FROM complaints WHERE user_id=? ORDER BY created_at DESC",
        (session["user_id"],)).fetchall()
    return render_template("student_dashboard.html", complaints=complaints)

@app.route("/complaint/new", methods=["GET", "POST"])
@login_required("student")
def new_complaint():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "")
        description = request.form.get("description", "").strip()
        allowed = ["Classroom", "Laboratory", "Hostel", "Library", "Transport", "Canteen", "Other"]
        if not title or category not in allowed or len(description) < 10:
            flash("Please complete all fields. Description must be at least 10 characters.", "danger")
        else:
            db = get_db()
            db.execute("INSERT INTO complaints(user_id,title,category,description) VALUES(?,?,?,?)",
                       (session["user_id"], title, category, description))
            db.commit()
            flash("Your complaint was submitted successfully.", "success")
            return redirect(url_for("student_dashboard"))
    return render_template("new_complaint.html")

@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    complaints = get_db().execute("""
        SELECT complaints.*, users.name AS student_name, users.email AS student_email
        FROM complaints JOIN users ON complaints.user_id=users.id
        ORDER BY complaints.created_at DESC
    """).fetchall()
    counts = {
        "total": len(complaints),
        "pending": sum(c["status"] == "Pending" for c in complaints),
        "progress": sum(c["status"] == "In Progress" for c in complaints),
        "resolved": sum(c["status"] == "Resolved" for c in complaints)
    }
    return render_template("admin_dashboard.html", complaints=complaints, counts=counts)

@app.route("/admin/complaint/<int:complaint_id>", methods=["POST"])
@login_required("admin")
def update_complaint(complaint_id):
    status = request.form.get("status")
    reply = request.form.get("admin_reply", "").strip()
    if status not in ["Pending", "In Progress", "Resolved"]:
        flash("Invalid status.", "danger")
    else:
        db = get_db()
        db.execute("UPDATE complaints SET status=?, admin_reply=? WHERE id=?",
                   (status, reply, complaint_id))
        db.commit()
        flash("Complaint updated.", "success")
    return redirect(url_for("admin_dashboard"))

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
