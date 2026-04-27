from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
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

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor = db.cursor()
        sql = "SELECT user_id, password_hash, user_role FROM user_accounts WHERE user_id = %s"
        cursor.execute(sql, [username])
        account = cursor.fetchone()
        cursor.close()

        if account and check_password_hash(account[1], password):
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


def is_admin():
    return "loggedin" in session and session["role"] == "admin"


def is_instructor():
    return "loggedin" in session and session["role"] == "instructor"


def is_student():
    return "loggedin" in session and session["role"] == "student"


@app.route("/admin")
def admin():
    if is_admin():
        return render_template("admin.html", user_id=session["user_id"])
    return redirect(url_for("login"))


@app.route("/instructor")
def instructor():
    if is_instructor():
        return render_template("instructor.html", user_id=session["user_id"])
    return redirect(url_for("login"))


@app.route("/student")
def student():
    if is_student():
        return render_template("student.html", user_id=session["user_id"])
    return redirect(url_for("login"))


# ---------------- ADMIN ROUTES ----------------

@app.route("/admin/courses", methods=["GET", "POST"])
def admin_courses():
    if not is_admin():
        return redirect(url_for("login"))

    data = []
    msg = ""

    if request.method == "POST":
        action = request.form["action"]

        cursor = db.cursor()

        if action == "read":
            cursor.callproc("Read_Course", [request.form["course_id"]])
            data = cursor.fetchall()

        elif action == "create":
            cursor.callproc("Create_Course", [
                request.form["course_id"],
                request.form["title"],
                request.form["dept_name"],
                request.form["credits"]
            ])
            db.commit()
            msg = "Course created."

        elif action == "update":
            cursor.callproc("Update_Course", [
                request.form["course_id"],
                request.form["title"],
                request.form["dept_name"],
                request.form["credits"]
            ])
            db.commit()
            msg = "Course updated."

        elif action == "delete":
            cursor.callproc("Delete_Course", [request.form["course_id"]])
            db.commit()
            msg = "Course deleted."

        cursor.close()

    return render_template("admin.html", page="courses", data=data, msg=msg, user_id=session["user_id"])


@app.route("/admin/students", methods=["GET", "POST"])
def admin_students():
    if not is_admin():
        return redirect(url_for("login"))

    data = []
    msg = ""

    if request.method == "POST":
        action = request.form["action"]
        cursor = db.cursor()

        if action == "read":
            cursor.callproc("Read_Student", [request.form["student_id"]])
            data = cursor.fetchall()

        elif action == "create":
            password_hash = generate_password_hash(request.form["password"])
            cursor.callproc("Create_Student", [
                request.form["student_id"],
                request.form["first_name"],
                request.form["middle_name"],
                request.form["last_name"],
                request.form["dept_name"],
                request.form["tot_cred"],
                request.form["advisor_id"],
                password_hash
            ])
            db.commit()
            msg = "Student created."

        elif action == "update":
            password_hash = generate_password_hash(request.form["password"])
            cursor.callproc("Update_Student", [
                request.form["student_id"],
                request.form["first_name"],
                request.form["middle_name"],
                request.form["last_name"],
                request.form["dept_name"],
                request.form["tot_cred"],
                request.form["advisor_id"],
                password_hash
            ])
            db.commit()
            msg = "Student updated."

        elif action == "delete":
            cursor.callproc("Delete_Student", [request.form["student_id"]])
            db.commit()
            msg = "Student deleted."

        cursor.close()

    return render_template("admin.html", page="students", data=data, msg=msg, user_id=session["user_id"])


@app.route("/admin/instructors", methods=["GET", "POST"])
def admin_instructors():
    if not is_admin():
        return redirect(url_for("login"))

    data = []
    msg = ""

    if request.method == "POST":
        action = request.form["action"]
        cursor = db.cursor()

        if action == "read":
            cursor.callproc("Read_Instructor", [request.form["instructor_id"]])
            data = cursor.fetchall()

        elif action == "create":
            password_hash = generate_password_hash(request.form["password"])
            cursor.callproc("Create_Instructor", [
                request.form["instructor_id"],
                request.form["first_name"],
                request.form["middle_name"],
                request.form["last_name"],
                request.form["dept_name"],
                request.form["salary"],
                password_hash
            ])
            db.commit()
            msg = "Instructor created."

        elif action == "update":
            password_hash = generate_password_hash(request.form["password"])
            cursor.callproc("Update_Instructor", [
                request.form["instructor_id"],
                request.form["first_name"],
                request.form["middle_name"],
                request.form["last_name"],
                request.form["dept_name"],
                request.form["salary"],
                password_hash
            ])
            db.commit()
            msg = "Instructor updated."

        elif action == "delete":
            cursor.callproc("Delete_Instructor", [request.form["instructor_id"]])
            db.commit()
            msg = "Instructor deleted."

        cursor.close()

    return render_template("admin.html", page="instructors", data=data, msg=msg, user_id=session["user_id"])


@app.route("/admin/assign-teacher", methods=["GET", "POST"])
def assign_teacher():
    if not is_admin():
        return redirect(url_for("login"))

    msg = ""

    if request.method == "POST":
        cursor = db.cursor()
        cursor.callproc("Assign_Teacher", [
            request.form["instructor_id"],
            request.form["course_id"],
            request.form["sec_id"],
            request.form["semester"],
            request.form["sec_year"]
        ])
        db.commit()
        cursor.close()
        msg = "Teacher assigned."

    return render_template("admin.html", page="assign_teacher", msg=msg, user_id=session["user_id"])


# ---------------- INSTRUCTOR ROUTES ----------------

@app.route("/instructor/sections", methods=["GET", "POST"])
def instructor_sections():
    if not is_instructor():
        return redirect(url_for("login"))

    data = []
    msg = ""

    if request.method == "POST":
        cursor = db.cursor()
        cursor.callproc("Check_Instructor_Section", [
            session["user_id"],
            request.form["semester"],
            request.form["sec_year"]
        ])
        data = cursor.fetchall()
        cursor.close()

        if not data:
            msg = "No sections found."

    return render_template("instructor.html", page="sections", data=data, msg=msg, user_id=session["user_id"])


@app.route("/instructor/roster", methods=["GET", "POST"])
def instructor_roster():
    if not is_instructor():
        return redirect(url_for("login"))

    data = []
    msg = ""

    if request.method == "POST":
        cursor = db.cursor()
        cursor.callproc("Check_Section_Roster", [
            request.form["course_id"],
            request.form["sec_id"],
            request.form["semester"],
            request.form["sec_year"]
        ])
        data = cursor.fetchall()
        cursor.close()

    return render_template("instructor.html", page="roster", data=data, msg=msg, user_id=session["user_id"])


@app.route("/instructor/submit-grade", methods=["GET", "POST"])
def submit_grade():
    if not is_instructor():
        return redirect(url_for("login"))

    msg = ""

    if request.method == "POST":
        cursor = db.cursor()
        cursor.callproc("Submit_Grade", [
            request.form["student_id"],
            request.form["course_id"],
            request.form["sec_id"],
            request.form["semester"],
            request.form["sec_year"],
            request.form["grade"]
        ])
        db.commit()
        cursor.close()
        msg = "Grade submitted."

    return render_template("instructor.html", page="submit_grade", msg=msg, user_id=session["user_id"])


@app.route("/instructor/change-grade", methods=["GET", "POST"])
def change_grade():
    if not is_instructor():
        return redirect(url_for("login"))

    msg = ""

    if request.method == "POST":
        cursor = db.cursor()
        cursor.callproc("Change_Grade", [
            request.form["student_id"],
            request.form["course_id"],
            request.form["sec_id"],
            request.form["semester"],
            request.form["sec_year"],
            request.form["grade"]
        ])
        db.commit()
        cursor.close()
        msg = "Grade changed."

    return render_template("instructor.html", page="change_grade", msg=msg, user_id=session["user_id"])


@app.route("/instructor/advisor", methods=["GET", "POST"])
def instructor_advisor():
    if not is_instructor():
        return redirect(url_for("login"))

    msg = ""

    if request.method == "POST":
        action = request.form["action"]
        cursor = db.cursor()

        if action == "add":
            cursor.callproc("Add_Advisor", [request.form["student_id"], session["user_id"]])
            msg = "Student added as advisee."

        elif action == "remove":
            cursor.callproc("Remove_Advisor", [request.form["student_id"]])
            msg = "Student removed as advisee."

        db.commit()
        cursor.close()

    return render_template("instructor.html", page="advisor", msg=msg, user_id=session["user_id"])


@app.route("/instructor/prereq", methods=["GET", "POST"])
def instructor_prereq():
    if not is_instructor():
        return redirect(url_for("login"))

    msg = ""

    if request.method == "POST":
        action = request.form["action"]
        cursor = db.cursor()

        if action == "add":
            cursor.callproc("Add_Prereq", [request.form["course_id"], request.form["prereq_id"]])
            msg = "Prerequisite added."

        elif action == "remove":
            cursor.callproc("Remove_Prereq", [request.form["course_id"], request.form["prereq_id"]])
            msg = "Prerequisite removed."

        db.commit()
        cursor.close()

    return render_template("instructor.html", page="prereq", msg=msg, user_id=session["user_id"])


# ---------------- STUDENT ROUTES ----------------

@app.route("/student/courses")
def student_courses():
    if not is_student():
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

    return render_template("student.html", page="courses", data=data, user_id=session["user_id"])


@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if not is_student():
        return redirect(url_for("login"))

    msg = ""

    if request.method == "POST":
        cursor = db.cursor()
        cursor.callproc("Enroll_Section", [
            session["user_id"],
            request.form["course_id"],
            request.form["sec_id"],
            request.form["semester"],
            request.form["sec_year"]
        ])
        db.commit()
        cursor.close()
        msg = "Registered for class."

    return render_template("student.html", page="register", msg=msg, user_id=session["user_id"])


@app.route("/student/drop", methods=["GET", "POST"])
def student_drop():
    if not is_student():
        return redirect(url_for("login"))

    msg = ""

    if request.method == "POST":
        cursor = db.cursor()
        cursor.callproc("Drop_Section", [
            session["user_id"],
            request.form["course_id"],
            request.form["sec_id"],
            request.form["semester"],
            request.form["sec_year"]
        ])
        db.commit()
        cursor.close()
        msg = "Class dropped."

    return render_template("student.html", page="drop", msg=msg, user_id=session["user_id"])


@app.route("/student/advisor")
def student_advisor():
    if not is_student():
        return redirect(url_for("login"))

    cursor = db.cursor()
    cursor.callproc("Check_Student_Advisor", [session["user_id"]])
    data = cursor.fetchall()
    cursor.close()

    return render_template("student.html", page="advisor", data=data, user_id=session["user_id"])


# ---------------- EXTRA QUERIES ----------------

@app.route("/admin/reports", methods=["GET", "POST"])
def reports():
    if not is_admin():
        return redirect(url_for("login"))

    data = []
    msg = ""

    if request.method == "POST":
        report_type = request.form["report_type"]
        cursor = db.cursor()

        if report_type == "avg_dept":
            cursor.callproc("Average_Grade_Department", [request.form["dept_name"]])

        elif report_type == "avg_course_range":
            cursor.callproc("Average_Grade_Range", [
                request.form["course_id"],
                request.form["start_year"],
                request.form["end_year"]
            ])

        elif report_type == "best_worst":
            cursor.callproc("Best_Worst_Sem", [
                request.form["semester"],
                request.form["sec_year"],
                request.form["mode"]
            ])

        elif report_type == "total_students_dept":
            cursor.callproc("Tot_Students_Department", [request.form["dept_name"]])

        elif report_type == "current_students_dept":
            cursor.callproc("Current_In_Department", [request.form["dept_name"]])

        data = cursor.fetchall()
        cursor.close()

    return render_template("admin.html", page="reports", data=data, msg=msg, user_id=session["user_id"])


if __name__ == "__main__":
    app.run(port=4500)