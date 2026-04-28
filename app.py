from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
import config

app = Flask(__name__)
app.debug = True
app.secret_key = "secret_key"
db = config.dbserver

def role_required(required_role):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if "loggedin" not in session or session.get("role") != required_role:
                flash("Access Denied", "secondary")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        cursor = db.cursor()
        cursor.execute("SELECT user_id, password_hash, user_role FROM user_accounts WHERE user_id = %s", [username])
        account = cursor.fetchone()
        cursor.close()
        if account and check_password_hash(account[1], password):
            session["loggedin"] = True
            session["user_id"] = account[0]
            session["role"] = account[2]
            return redirect(url_for(account[2]))
        msg = "Incorrect username or password."
    return render_template("login.html", msg=msg)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/student")
@role_required("student")
def student():
    return render_template("student.html", user_id=session["user_id"])

@app.route("/student/courses")
@role_required("student")
def student_courses():
    student_id = session["user_id"]
    cursor = db.cursor()
    cursor.execute("SELECT t.course_id, c.title, t.sec_id, t.semester, t.sec_year, t.grade FROM takes t JOIN course c ON t.course_id = c.course_id WHERE t.student_id = %s ORDER BY t.sec_year DESC, t.semester", [student_id])
    data = cursor.fetchall()
    cursor.close()
    return render_template("student.html", user_id=session["user_id"], data=data, page="courses")

@app.route("/student/advisor")
@role_required("student")
def student_advisor():
    student_id = session["user_id"]
    cursor = db.cursor()
    cursor.execute("SELECT i.instructor_id, i.first_name, i.middle_name, i.last_name, i.dept_name FROM student s JOIN instructor i ON s.advisor_id = i.instructor_id WHERE s.student_id = %s", [student_id])
    data = cursor.fetchall()
    cursor.close()
    return render_template("student.html", user_id=session["user_id"], data=data, page="advisor")

@app.route("/student/enroll", methods=["GET", "POST"])
@role_required("student")
def student_enroll():
    student_id = session["user_id"]
    if request.method == "POST":
        cursor = db.cursor()
        cursor.callproc("Enroll_Section", [student_id, request.form["course_id"], request.form["sec_id"], request.form["semester"], int(request.form["sec_year"])])
        db.commit()
        cursor.close()
        flash("Enrolled successfully", "success")
        return redirect(url_for("student_courses"))
    cursor = db.cursor()
    cursor.execute("SELECT s.course_id, c.title, s.sec_id, s.semester, s.sec_year, s.building, s.room_number FROM section s JOIN course c ON s.course_id = c.course_id WHERE (s.course_id, s.sec_id, s.semester, s.sec_year) NOT IN (SELECT course_id, sec_id, semester, sec_year FROM takes WHERE student_id = %s) LIMIT 30", [student_id])
    available = cursor.fetchall()
    cursor.close()
    return render_template("student_enroll.html", user_id=student_id, available=available)

@app.route("/student/drop", methods=["POST"])
@role_required("student")
def student_drop():
    student_id = session["user_id"]
    cursor = db.cursor()
    cursor.callproc("Drop_Section", [student_id, request.form["course_id"], request.form["sec_id"], request.form["semester"], int(request.form["sec_year"])])
    db.commit()
    cursor.close()
    flash("Course dropped", "success")
    return redirect(url_for("student_courses"))

@app.route("/student/personal")
@role_required("student")
def student_personal():
    flash("Modify personal info form coming soon hopefully", "info")
    return redirect(url_for("student"))

if __name__ == "__main__":
    app.run(port=4500)