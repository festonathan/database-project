from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
import config

app = Flask(__name__)
app.debug = True
app.secret_key = "secret_key"

db = config.dbserver

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""

    if request.method == "GET":
        return render_template("login.html", msg=msg)

    username = request.form["username"]
    user_password = request.form["password"]

    cursor = db.cursor()
    sql = "SELECT user_id, password_hash, user_role FROM user_accounts WHERE user_id = %s"
    cursor.execute(sql, [username])
    account = cursor.fetchone()
    cursor.close()

    if account and check_password_hash(account[1], user_password):
        session["loggedin"] = True
        session["user_id"] = account[0]
        session["role"] = account[2]

        if account[2] == "admin":
            return redirect(url_for("admin"))
        elif account[2] == "instructor":
            return redirect(url_for("instructor"))
        elif account[2] == "student":
            return redirect(url_for("student"))

    msg = "Incorrect username or password."
    return render_template("login.html", msg=msg)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/admin")
def admin():
    if "loggedin" in session and session["role"] == "admin":
        return render_template("admin.html", user_id=session["user_id"])
    return redirect(url_for("login"))


@app.route("/admin/courses", methods=["GET", "POST"])
def admin_courses():
    if "loggedin" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    data = []
    msg = ""

    if request.method == "POST":
        course_id = request.form["course_id"]

        cursor = db.cursor()
        cursor.callproc("Read_Course", [course_id])
        data = cursor.fetchall()
        cursor.close()

        if not data:
            msg = "No course found."

    return render_template("admin.html", user_id=session["user_id"], data=data, page="courses", msg=msg)


@app.route("/admin/students")
def admin_students():
    if "loggedin" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    cursor = db.cursor()
    sql = "SELECT student_id, first_name, middle_name, last_name, dept_name, tot_cred, advisor_id FROM student"
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()

    return render_template("admin.html", user_id=session["user_id"], data=data, page="students")


@app.route("/admin/instructors")
def admin_instructors():
    if "loggedin" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    cursor = db.cursor()
    sql = "SELECT instructor_id, first_name, middle_name, last_name, dept_name, salary FROM instructor"
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()

    return render_template("admin.html", user_id=session["user_id"], data=data, page="instructors")


@app.route("/instructor")
def instructor():
    if "loggedin" in session and session["role"] == "instructor":
        return render_template("instructor.html", user_id=session["user_id"])
    return redirect(url_for("login"))


@app.route("/instructor/sections", methods=["GET", "POST"])
def instructor_sections():
    if "loggedin" not in session or session["role"] != "instructor":
        return redirect(url_for("login"))

    data = []
    msg = ""

    if request.method == "POST":
        semester = request.form["semester"]
        sec_year = request.form["sec_year"]

        cursor = db.cursor()
        cursor.callproc("Check_Instructor_Section", [session["user_id"], semester, sec_year])
        data = cursor.fetchall()
        cursor.close()

        if not data:
            msg = "No sections found."

    return render_template("instructor.html", user_id=session["user_id"], data=data, page="sections", msg=msg)


@app.route("/instructor/roster", methods=["GET", "POST"])
def instructor_roster():
    if "loggedin" not in session or session["role"] != "instructor":
        return redirect(url_for("login"))

    data = []
    msg = ""

    if request.method == "POST":
        course_id = request.form["course_id"]
        sec_id = request.form["sec_id"]
        semester = request.form["semester"]
        sec_year = request.form["sec_year"]

        cursor = db.cursor()
        cursor.callproc("Check_Section_Roster", [course_id, sec_id, semester, sec_year])
        data = cursor.fetchall()
        cursor.close()

        if not data:
            msg = "No roster found."

    return render_template("instructor.html", user_id=session["user_id"], data=data, page="roster", msg=msg)


@app.route("/student")
def student():
    if "loggedin" in session and session["role"] == "student":
        return render_template("student.html", user_id=session["user_id"])
    return redirect(url_for("login"))


@app.route("/student/courses")
def student_courses():
    if "loggedin" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    cursor = db.cursor()
    sql = """
        SELECT t.course_id, c.title, t.sec_id, t.semester, t.sec_year, t.grade
        FROM takes t, course c
        WHERE t.course_id = c.course_id
        AND t.student_id = %s
        ORDER BY t.sec_year, t.semester
    """
    cursor.execute(sql, [session["user_id"]])
    data = cursor.fetchall()
    cursor.close()

    return render_template("student.html", user_id=session["user_id"], data=data, page="courses")


@app.route("/student/advisor")
def student_advisor():
    if "loggedin" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    cursor = db.cursor()
    cursor.callproc("Check_Student_Advisor", [session["user_id"]])
    data = cursor.fetchall()
    cursor.close()

    return render_template("student.html", user_id=session["user_id"], data=data, page="advisor")


if __name__ == "__main__":
    app.run(port=4500)