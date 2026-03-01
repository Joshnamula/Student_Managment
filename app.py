from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secretkey"  # required for sessions and flash messages

# ------------------- DATABASE ------------------- #
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            marks INTEGER NOT NULL,
            grade TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------- SERVE CSS ------------------- #
@app.route("/style.css")
def serve_css():
    return send_from_directory(os.getcwd(), "style.css")

# ------------------- LOGIN REQUIRED DECORATOR ------------------- #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please login first!", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ------------------- GRADE CALCULATION ------------------- #
def calculate_grade(marks):
    if marks >= 90:
        return "A"
    elif marks >= 75:
        return "B"
    elif marks >= 50:
        return "C"
    else:
        return "Fail"

# ------------------- LOGIN ------------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Simple hardcoded credentials
        if username == "admin" and password == "admin":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid Username or Password!", "danger")
    
    return render_template("login.html")

# ------------------- LOGOUT ------------------- #
@app.route("/logout")
@login_required
def logout():
    session.pop("logged_in", None)
    flash("You have been logged out!", "info")
    return redirect(url_for("login"))

# ------------------- ROOT ------------------- #
@app.route("/")
def root():
    return redirect(url_for("login"))

# ------------------- DASHBOARD ------------------- #
# ------------------- DASHBOARD ------------------- #
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    
    # Fetch all students to display below the card (or latest 10 for dashboard)
    students = conn.execute("SELECT * FROM students ORDER BY id DESC LIMIT 10").fetchall()
    
    conn.close()
    return render_template("home.html", total_students=total_students, students=students)

# ------------------- ADD STUDENT ------------------- #
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        roll_no = request.form["roll_no"]
        name = request.form["name"]
        marks = int(request.form["marks"])

        if marks < 0 or marks > 100:
            flash("Marks must be between 0 and 100!", "danger")
            return redirect(url_for("add_student"))

        grade = calculate_grade(marks)

        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO students (roll_no, name, marks, grade) VALUES (?, ?, ?, ?)",
                (roll_no, name, marks, grade)
            )
            conn.commit()
            conn.close()
            flash("Student added successfully!", "success")
        except:
            flash("Roll number already exists!", "danger")

        return redirect(url_for("view_students"))

    return render_template("add_student.html")

# ------------------- VIEW STUDENTS ------------------- #
@app.route("/students")
@login_required
def view_students():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template("view_students.html", students=students)

# ------------------- SEARCH STUDENT ------------------- #
@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        roll_no = request.form["roll_no"]
        conn = get_db_connection()
        student = conn.execute(
            "SELECT * FROM students WHERE roll_no = ?",
            (roll_no,)
        ).fetchone()
        conn.close()
        return render_template("result.html", student=student)

    return render_template("search.html")

# ------------------- UPDATE STUDENT ------------------- #
@app.route("/update/<int:id>", methods=["GET", "POST"])
@login_required
def update_student(id):
    conn = get_db_connection()
    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        marks = int(request.form["marks"])
        grade = calculate_grade(marks)

        conn.execute(
            "UPDATE students SET name=?, marks=?, grade=? WHERE id=?",
            (name, marks, grade, id)
        )
        conn.commit()
        conn.close()
        flash("Student updated successfully!", "info")
        return redirect(url_for("view_students"))

    conn.close()
    return render_template("update_student.html", student=student)

# ------------------- DELETE STUDENT ------------------- #
@app.route("/delete/<int:id>")
@login_required
def delete_student(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Student deleted!", "warning")
    return redirect(url_for("view_students"))

# ------------------- RUN APP ------------------- #
if __name__ == "__main__":
    app.run()
    