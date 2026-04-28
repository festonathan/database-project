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

@app.route("/admin")
@role_required("admin")
def admin():
    return render_template("admin.html", user_id=session["user_id"])

@app.route("/instructor")
@role_required("instructor")
def instructor():
    return render_template("instructor.html", user_id=session["user_id"])

@app.route("/instructor/sections")
@role_required("instructor")
def instructor_sections():
    instructor_id = session["user_id"]
    semester = request.args.get("semester")
    sec_year = request.args.get("sec_year")
    cursor = db.cursor()
    if semester and sec_year:
        cursor.callproc("Check_Instructor_Section", [instructor_id, semester, int(sec_year)])
    else:
        cursor.execute("SELECT t.course_id, c.title, t.sec_id, t.semester, t.sec_year FROM teaches t JOIN course c ON t.course_id = c.course_id WHERE t.instructor_id = %s ORDER BY t.sec_year DESC, t.semester", [instructor_id])
    data = cursor.fetchall()
    cursor.close()
    return render_template("instructor.html", user_id=session["user_id"], data=data, page="sections", filter_semester=semester, filter_year=sec_year)

@app.route("/instructor/roster", methods=["GET", "POST"])
@role_required("instructor")
def instructor_roster():
    course_id = None
    sec_id = None
    semester = None
    sec_year = None
    data = None
    if request.method == "POST":
        course_id = request.form.get("course_id")
        sec_id = request.form.get("sec_id")
        semester = request.form.get("semester")
        sec_year = request.form.get("sec_year")
        if course_id and sec_id and semester and sec_year:
            cursor = db.cursor()
            cursor.callproc("Check_Section_Roster", [course_id, sec_id, semester, int(sec_year)])
            data = cursor.fetchall()
            cursor.close()
    elif request.method == "GET":
        course_id = request.args.get("course_id")
        sec_id = request.args.get("sec_id")
        semester = request.args.get("semester")
        sec_year = request.args.get("sec_year")
        if course_id and sec_id and semester and sec_year:
            cursor = db.cursor()
            cursor.callproc("Check_Section_Roster", [course_id, sec_id, semester, int(sec_year)])
            data = cursor.fetchall()
            cursor.close()
    return render_template("instructor.html", user_id=session["user_id"], data=data, page="roster",
                           course_id=course_id, sec_id=sec_id, semester=semester, sec_year=sec_year)

@app.route("/instructor/submit_grade", methods=["POST"])
@role_required("instructor")
def instructor_submit_grade():
    course_id = request.form.get("course_id")
    sec_id = request.form.get("sec_id")
    semester = request.form.get("semester")
    sec_year = request.form.get("sec_year")
    cursor = db.cursor()
    cursor.callproc("Submit_Grade", [request.form["student_id"], course_id, sec_id, semester, int(sec_year), request.form["grade"]])
    db.commit()
    cursor.close()
    flash("Grade updated", "secondary")
    return redirect(url_for("instructor_roster", course_id=course_id, sec_id=sec_id, semester=semester, sec_year=sec_year))

@app.route("/instructor/remove_student", methods=["POST"])
@role_required("instructor")
def instructor_remove_student():
    student_id = request.form.get("student_id")
    course_id = request.form.get("course_id")
    sec_id = request.form.get("sec_id")
    semester = request.form.get("semester")
    sec_year = request.form.get("sec_year")
    try:
        cursor = db.cursor()
        cursor.callproc("Drop_Section", [student_id, course_id, sec_id, semester, int(sec_year)])
        db.commit()
        cursor.close()
        flash("Student removed from section", "secondary")
    except Exception as e:
        err = str(e).lower()
        if "1062" in err or "duplicate" in err:
            flash("Error: duplicate entry", "secondary")
        else:
            flash("Error: invalid input", "secondary")
    return redirect(url_for("instructor_roster", course_id=course_id, sec_id=sec_id, semester=semester, sec_year=sec_year))

@app.route("/instructor/add_advisor", methods=["POST"])
@role_required("instructor")
def instructor_add_advisor():
    student_id = request.form.get("student_id")
    instructor_id = session["user_id"]
    try:
        cursor = db.cursor()
        cursor.execute("SELECT advisor_id FROM student WHERE student_id = %s", (student_id,))
        current = cursor.fetchone()
        cursor.close()
        if current and current[0] == instructor_id:
            flash("Error: duplicate entry - student is already your advisee", "secondary")
            return redirect(url_for("instructor_advising"))
        cursor = db.cursor()
        cursor.callproc("Add_Advisor", [student_id, instructor_id])
        db.commit()
        cursor.close()
        cursor = db.cursor()
        cursor.execute("SELECT advisor_id FROM student WHERE student_id = %s", (student_id,))
        result = cursor.fetchone()
        cursor.close()
        if result and result[0] == instructor_id:
            flash("Student added as advisee successfully", "secondary")
        else:
            flash("Failed to add advisee. Student ID may be invalid or does not exist in the database.", "secondary")
    except Exception as e:
        err = str(e).lower()
        if "1062" in err or "duplicate" in err:
            flash("Error: duplicate entry", "secondary")
        elif "1452" in err or "foreign key" in err:
            flash("Error: invalid id or reference", "secondary")
        else:
            flash("Error: invalid input", "secondary")
    return redirect(url_for("instructor_advising"))

@app.route("/instructor/remove_advisor", methods=["POST"])
@role_required("instructor")
def instructor_remove_advisor():
    student_id = request.form.get("student_id")
    try:
        cursor = db.cursor()
        cursor.callproc("Remove_Advisor", [student_id])
        db.commit()
        cursor.close()
        cursor = db.cursor()
        cursor.execute("SELECT advisor_id FROM student WHERE student_id = %s", (student_id,))
        result = cursor.fetchone()
        cursor.close()
        if result and result[0] is None:
            flash("Student removed from advising successfully", "secondary")
        else:
            flash("Failed to remove advisee. Student ID may be invalid.", "secondary")
    except Exception as e:
        err = str(e).lower()
        if "1062" in err or "duplicate" in err:
            flash("Error: duplicate entry", "secondary")
        elif "1452" in err or "foreign key" in err:
            flash("Error: invalid id or reference", "secondary")
        else:
            flash("Error: invalid input", "secondary")
    return redirect(url_for("instructor_advising"))

@app.route("/instructor/add_prereq", methods=["POST"])
@role_required("instructor")
def instructor_add_prereq():
    try:
        cursor = db.cursor()
        cursor.callproc("Add_Prereq", [request.form["course_id"], request.form["prereq_id"]])
        db.commit()
        cursor.close()
        flash("Prerequisite added successfully", "secondary")
    except Exception as e:
        err = str(e).lower()
        if "1062" in err or "duplicate" in err:
            flash("Error: duplicate entry", "secondary")
        elif "1452" in err or "foreign key" in err:
            flash("Error: invalid id or reference", "secondary")
        else:
            flash("Error: invalid input", "secondary")
    return redirect(url_for("instructor_prereqs"))

@app.route("/instructor/remove_prereq", methods=["POST"])
@role_required("instructor")
def instructor_remove_prereq():
    course_id = request.form.get("course_id")
    prereq_id = request.form.get("prereq_id")
    try:
        cursor = db.cursor()
        cursor.callproc("Remove_Prereq", [course_id, prereq_id])
        db.commit()
        cursor.close()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM prereq WHERE course_id = %s AND prereq_id = %s", (course_id, prereq_id))
        count = cursor.fetchone()[0]
        cursor.close()
        if count == 0:
            flash("Prerequisite removed successfully", "secondary")
        else:
            flash("Failed to remove prerequisite. It may not have existed.", "secondary")
    except Exception as e:
        err = str(e).lower()
        if "1062" in err or "duplicate" in err:
            flash("Error: duplicate entry", "secondary")
        elif "1452" in err or "foreign key" in err:
            flash("Error: invalid id or reference", "secondary")
        else:
            flash("Error: invalid input", "secondary")
    return redirect(url_for("instructor_prereqs"))

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
        try:
            cursor = db.cursor()
            cursor.callproc("Enroll_Section", [student_id, request.form["course_id"], request.form["sec_id"], request.form["semester"], int(request.form["sec_year"])])
            db.commit()
            cursor.close()
            flash("Enrolled successfully", "secondary")
            return redirect(url_for("student_courses"))
        except Exception as e:
            err = str(e).lower()
            if "1062" in err or "duplicate" in err:
                flash("Error: duplicate entry - you are already enrolled in this section", "secondary")
            else:
                flash("Error: invalid input or section not available", "secondary")
            return redirect(url_for("student_enroll"))
    cursor = db.cursor()
    cursor.execute("SELECT s.course_id, c.title, s.sec_id, s.semester, s.sec_year, s.building, s.room_number FROM section s JOIN course c ON s.course_id = c.course_id WHERE (s.course_id, s.sec_id, s.semester, s.sec_year) NOT IN (SELECT course_id, sec_id, semester, sec_year FROM takes WHERE student_id = %s) LIMIT 30", [student_id])
    available = cursor.fetchall()
    cursor.close()
    return render_template("student_enroll.html", user_id=student_id, available=available)

@app.route("/student/drop", methods=["POST"])
@role_required("student")
def student_drop():
    student_id = session["user_id"]
    try:
        cursor = db.cursor()
        cursor.callproc("Drop_Section", [student_id, request.form["course_id"], request.form["sec_id"], request.form["semester"], int(request.form["sec_year"])])
        db.commit()
        cursor.close()
        flash("Course dropped", "secondary")
        return redirect(url_for("student_courses"))
    except Exception as e:
        err = str(e).lower()
        if "1062" in err or "duplicate" in err:
            flash("Error: duplicate entry", "secondary")
        else:
            flash("Error: invalid input", "secondary")
        return redirect(url_for("student_courses"))

@app.route("/student/personal")
@role_required("student")
def student_personal():
    flash("Modify personal info form coming hopefully", "secondary")
    return redirect(url_for("student"))

@app.route("/instructor/grades")
@role_required("instructor")
def instructor_grades():
    return redirect(url_for("instructor_sections"))

@app.route("/instructor/advising")
@role_required("instructor")
def instructor_advising():
    instructor_id = session["user_id"]
    cursor = db.cursor()
    cursor.execute("SELECT student_id, first_name, middle_name, last_name, dept_name FROM student WHERE advisor_id = %s", [instructor_id])
    advisees = cursor.fetchall()
    cursor.close()
    return render_template("instructor.html", user_id=instructor_id, page="advising", advisees=advisees)

@app.route("/instructor/prereqs")
@role_required("instructor")
def instructor_prereqs():
    return render_template("instructor.html", user_id=session["user_id"], page="prereqs")

@app.route("/instructor/personal")
@role_required("instructor")
def instructor_personal():
    flash("Modify personal info form - I don't think I can in time", "secondary")
    return redirect(url_for("instructor"))

if __name__ == "__main__":
    app.run(port=4500)