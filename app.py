"""
ResumeCraft - Automatic Resume Builder
Base starter application (Flask + SQLite + ReportLab)

Run:
    python app.py
Then open http://127.0.0.1:5000 in Chrome.
"""

import os
import sqlite3
import json
from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, send_file, g
)
from werkzeug.security import generate_password_hash, check_password_hash

from utils.pdf_generator import generate_resume_pdf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)
app.secret_key = "change-this-secret-key-before-deployment"  # TODO: move to env var

TEMPLATES = ["modern", "professional", "minimal"]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            template TEXT NOT NULL,
            data TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            flash("An account with this email already exists.", "error")
            return redirect(url_for("register"))

        db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, generate_password_hash(password), datetime.utcnow().isoformat()),
        )
        db.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("landing"))


# ---------------------------------------------------------------------------
# Dashboard / resume CRUD
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    resumes = db.execute(
        "SELECT id, title, template, updated_at FROM resumes WHERE user_id = ? ORDER BY updated_at DESC",
        (session["user_id"],),
    ).fetchall()
    return render_template("dashboard.html", resumes=resumes)


@app.route("/resumes")
@login_required
def my_resumes():
    db = get_db()
    resumes = db.execute(
        "SELECT id, title, template, updated_at FROM resumes WHERE user_id = ? ORDER BY updated_at DESC",
        (session["user_id"],),
    ).fetchall()
    return render_template("my_resumes.html", resumes=resumes)


@app.route("/resume/new", methods=["GET", "POST"])
@login_required
def create_resume():
    if request.method == "POST":
        payload = _resume_form_to_json(request.form)
        title = request.form.get("title", "Untitled Resume").strip()
        template = request.form.get("template", "modern")

        db = get_db()
        cur = db.execute(
            "INSERT INTO resumes (user_id, title, template, data, updated_at) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], title, template, json.dumps(payload), datetime.utcnow().isoformat()),
        )
        db.commit()
        flash("Resume created.", "success")
        return redirect(url_for("preview_resume", resume_id=cur.lastrowid))

    return render_template("create_resume.html", templates=TEMPLATES, resume=None, data={})


@app.route("/resume/<int:resume_id>/edit", methods=["GET", "POST"])
@login_required
def edit_resume(resume_id):
    db = get_db()
    resume = db.execute(
        "SELECT * FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, session["user_id"]),
    ).fetchone()
    if resume is None:
        flash("Resume not found.", "error")
        return redirect(url_for("my_resumes"))

    if request.method == "POST":
        payload = _resume_form_to_json(request.form)
        title = request.form.get("title", "Untitled Resume").strip()
        template = request.form.get("template", "modern")

        db.execute(
            "UPDATE resumes SET title = ?, template = ?, data = ?, updated_at = ? WHERE id = ?",
            (title, template, json.dumps(payload), datetime.utcnow().isoformat(), resume_id),
        )
        db.commit()
        flash("Resume updated.", "success")
        return redirect(url_for("preview_resume", resume_id=resume_id))

    data = json.loads(resume["data"])
    return render_template("create_resume.html", templates=TEMPLATES, resume=resume, data=data)


@app.route("/resume/<int:resume_id>/delete", methods=["POST"])
@login_required
def delete_resume(resume_id):
    db = get_db()
    db.execute(
        "DELETE FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, session["user_id"]),
    )
    db.commit()
    flash("Resume deleted.", "success")
    return redirect(url_for("my_resumes"))


@app.route("/resume/<int:resume_id>/preview")
@login_required
def preview_resume(resume_id):
    db = get_db()
    resume = db.execute(
        "SELECT * FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, session["user_id"]),
    ).fetchone()
    if resume is None:
        flash("Resume not found.", "error")
        return redirect(url_for("my_resumes"))

    data = json.loads(resume["data"])
    return render_template(
        "preview.html", resume=resume, data=data, template_name=resume["template"]
    )


@app.route("/resume/<int:resume_id>/download")
@login_required
def download_resume(resume_id):
    db = get_db()
    resume = db.execute(
        "SELECT * FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, session["user_id"]),
    ).fetchone()
    if resume is None:
        flash("Resume not found.", "error")
        return redirect(url_for("my_resumes"))

    data = json.loads(resume["data"])
    pdf_path = generate_resume_pdf(data, resume["template"], resume["title"])
    return send_file(pdf_path, as_attachment=True, download_name=f"{resume['title']}.pdf")


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        new_password = request.form.get("password", "").strip()

        if new_password:
            db.execute(
                "UPDATE users SET name = ?, password_hash = ? WHERE id = ?",
                (name, generate_password_hash(new_password), session["user_id"]),
            )
        else:
            db.execute(
                "UPDATE users SET name = ? WHERE id = ?",
                (name, session["user_id"]),
            )
        db.commit()
        session["user_name"] = name
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resume_form_to_json(form):
    """Convert the resume form submission into a structured dict."""
    return {
        "full_name": form.get("full_name", "").strip(),
        "email": form.get("email", "").strip(),
        "phone": form.get("phone", "").strip(),
        "linkedin": form.get("linkedin", "").strip(),
        "github": form.get("github", "").strip(),
        "objective": form.get("objective", "").strip(),
        "education": form.get("education", "").strip(),
        "skills": [s.strip() for s in form.get("skills", "").split(",") if s.strip()],
        "projects": form.get("projects", "").strip(),
        "experience": form.get("experience", "").strip(),
        "certifications": form.get("certifications", "").strip(),
        "paper_workshops": form.get("paper_workshops", "").strip(),
        "achievements": form.get("achievements", "").strip(),
        "languages": form.get("languages", "").strip(),
        "areas_of_interest": form.get("areas_of_interest", "").strip(),
    }


@app.context_processor
def inject_globals():
    return {"current_year": datetime.utcnow().year}


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    else:
        init_db()  # safe: CREATE TABLE IF NOT EXISTS
    app.run(debug=True)
