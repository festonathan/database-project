from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
import config

app = Flask(__name__)
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

@app.route("/admin/courses")
@role_required("admin")
def admin_courses():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM course")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="courses")

@app.route("/admin/course/create", methods=["POST"])
@role_required("admin")
def admin_create_course():
    try:
        cursor = db.cursor()
        cursor.callproc("Create_Course", [request.form.get("course_id"), request.form.get("title"), request.form.get("dept_name"), int(request.form.get("credits"))])
        db.commit()
        cursor.close()
        flash("Course created successfully", "secondary")
    except Exception:
        flash("Error creating course", "secondary")
    return redirect(url_for("admin_courses"))

@app.route("/admin/course/update", methods=["POST"])
@role_required("admin")
def admin_update_course():
    try:
        cursor = db.cursor()
        cursor.callproc("Update_Course", [request.form.get("course_id"), request.form.get("title"), request.form.get("dept_name"), int(request.form.get("credits"))])
        db.commit()
        cursor.close()
        flash("Course updated successfully", "secondary")
    except Exception:
        flash("Error updating course", "secondary")
    return redirect(url_for("admin_courses"))

@app.route("/admin/course/delete", methods=["POST"])
@role_required("admin")
def admin_delete_course():
    try:
        cursor = db.cursor()
        cursor.callproc("Delete_Course", [request.form.get("course_id")])
        db.commit()
        cursor.close()
        flash("Course deleted successfully", "secondary")
    except Exception:
        flash("Error deleting course. May be referenced by sections or prerequisites.", "secondary")
    return redirect(url_for("admin_courses"))

@app.route("/admin/students")
@role_required("admin")
def admin_students():
    cursor = db.cursor()
    cursor.execute("SELECT student_id, first_name, middle_name, last_name, dept_name, tot_cred, advisor_id FROM student")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="students")

@app.route("/admin/student/create", methods=["POST"])
@role_required("admin")
def admin_create_student():
    password = request.form.get("password")
    p_hash = generate_password_hash(password) if password else ""
    try:
        cursor = db.cursor()
        cursor.callproc("Create_Student", [
            request.form.get("student_id"),
            request.form.get("first_name"),
            request.form.get("middle_name") or "",
            request.form.get("last_name"),
            request.form.get("dept_name"),
            int(request.form.get("tot_cred") or 0),
            request.form.get("advisor_id") or None,
            p_hash
        ])
        db.commit()
        cursor.close()
        flash("Student created successfully", "secondary")
    except Exception:
        flash("Error creating student", "secondary")
    return redirect(url_for("admin_students"))

@app.route("/admin/student/update", methods=["POST"])
@role_required("admin")
def admin_update_student():
    password = request.form.get("password")
    p_hash = generate_password_hash(password) if password else request.form.get("password_hash")
    try:
        cursor = db.cursor()
        cursor.callproc("Update_Student", [
            request.form.get("student_id"),
            request.form.get("first_name"),
            request.form.get("middle_name") or "",
            request.form.get("last_name"),
            request.form.get("dept_name"),
            int(request.form.get("tot_cred") or 0),
            request.form.get("advisor_id") or None,
            p_hash
        ])
        db.commit()
        cursor.close()
        flash("Student updated successfully", "secondary")
    except Exception:
        flash("Error updating student", "secondary")
    return redirect(url_for("admin_students"))

@app.route("/admin/student/delete", methods=["POST"])
@role_required("admin")
def admin_delete_student():
    try:
        cursor = db.cursor()
        cursor.callproc("Delete_Student", [request.form.get("student_id")])
        db.commit()
        cursor.close()
        flash("Student deleted successfully", "secondary")
    except Exception:
        flash("Error deleting student", "secondary")
    return redirect(url_for("admin_students"))

@app.route("/admin/instructors")
@role_required("admin")
def admin_instructors():
    cursor = db.cursor()
    cursor.execute("SELECT instructor_id, first_name, middle_name, last_name, dept_name, salary FROM instructor")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="instructors")

@app.route("/admin/instructor/create", methods=["POST"])
@role_required("admin")
def admin_create_instructor():
    password = request.form.get("password")
    p_hash = generate_password_hash(password) if password else ""
    try:
        cursor = db.cursor()
        cursor.callproc("Create_Instructor", [
            request.form.get("instructor_id"),
            request.form.get("first_name"),
            request.form.get("middle_name") or "",
            request.form.get("last_name"),
            request.form.get("dept_name"),
            float(request.form.get("salary") or 0),
            p_hash
        ])
        db.commit()
        cursor.close()
        flash("Instructor created successfully", "secondary")
    except Exception:
        flash("Error creating instructor", "secondary")
    return redirect(url_for("admin_instructors"))

@app.route("/admin/instructor/update", methods=["POST"])
@role_required("admin")
def admin_update_instructor():
    password = request.form.get("password")
    p_hash = generate_password_hash(password) if password else request.form.get("password_hash")
    try:
        cursor = db.cursor()
        cursor.callproc("Update_Instructor", [
            request.form.get("instructor_id"),
            request.form.get("first_name"),
            request.form.get("middle_name") or "",
            request.form.get("last_name"),
            request.form.get("dept_name"),
            float(request.form.get("salary") or 0),
            p_hash
        ])
        db.commit()
        cursor.close()
        flash("Instructor updated successfully", "secondary")
    except Exception:
        flash("Error updating instructor", "secondary")
    return redirect(url_for("admin_instructors"))

@app.route("/admin/instructor/delete", methods=["POST"])
@role_required("admin")
def admin_delete_instructor():
    try:
        cursor = db.cursor()
        cursor.callproc("Delete_Instructor", [request.form.get("instructor_id")])
        db.commit()
        cursor.close()
        flash("Instructor deleted successfully", "secondary")
    except Exception:
        flash("Error deleting instructor. May be assigned to sections.", "secondary")
    return redirect(url_for("admin_instructors"))

@app.route("/admin/classrooms")
@role_required("admin")
def admin_classrooms():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM classroom")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="classrooms")

@app.route("/admin/classroom/create", methods=["POST"])
@role_required("admin")
def admin_create_classroom():
    try:
        cursor = db.cursor()
        cursor.callproc("Create_Classroom", [request.form.get("building"), request.form.get("room_number"), int(request.form.get("capacity"))])
        db.commit()
        cursor.close()
        flash("Classroom created successfully", "secondary")
    except Exception:
        flash("Error creating classroom", "secondary")
    return redirect(url_for("admin_classrooms"))

@app.route("/admin/classroom/update", methods=["POST"])
@role_required("admin")
def admin_update_classroom():
    try:
        cursor = db.cursor()
        cursor.callproc("Update_Classroom", [request.form.get("building"), request.form.get("room_number"), int(request.form.get("capacity"))])
        db.commit()
        cursor.close()
        flash("Classroom updated successfully", "secondary")
    except Exception:
        flash("Error updating classroom", "secondary")
    return redirect(url_for("admin_classrooms"))

@app.route("/admin/classroom/delete", methods=["POST"])
@role_required("admin")
def admin_delete_classroom():
    try:
        cursor = db.cursor()
        cursor.callproc("Delete_Classroom", [request.form.get("building"), request.form.get("room_number")])
        db.commit()
        cursor.close()
        flash("Classroom deleted successfully", "secondary")
    except Exception:
        flash("Error deleting classroom. May be referenced by sections.", "secondary")
    return redirect(url_for("admin_classrooms"))

@app.route("/admin/departments")
@role_required("admin")
def admin_departments():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM department")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="departments")

@app.route("/admin/department/create", methods=["POST"])
@role_required("admin")
def admin_create_department():
    try:
        cursor = db.cursor()
        cursor.callproc("Create_Department", [request.form.get("dept_name"), request.form.get("building"), float(request.form.get("budget") or 0)])
        db.commit()
        cursor.close()
        flash("Department created successfully", "secondary")
    except Exception:
        flash("Error creating department", "secondary")
    return redirect(url_for("admin_departments"))

@app.route("/admin/department/update", methods=["POST"])
@role_required("admin")
def admin_update_department():
    try:
        cursor = db.cursor()
        cursor.callproc("Update_Department", [request.form.get("dept_name"), request.form.get("building"), float(request.form.get("budget") or 0)])
        db.commit()
        cursor.close()
        flash("Department updated successfully", "secondary")
    except Exception:
        flash("Error updating department", "secondary")
    return redirect(url_for("admin_departments"))

@app.route("/admin/department/delete", methods=["POST"])
@role_required("admin")
def admin_delete_department():
    try:
        cursor = db.cursor()
        cursor.callproc("Delete_Department", [request.form.get("dept_name")])
        db.commit()
        cursor.close()
        flash("Department deleted successfully", "secondary")
    except Exception:
        flash("Error deleting department. May have associated courses or instructors.", "secondary")
    return redirect(url_for("admin_departments"))

@app.route("/admin/time_slots")
@role_required("admin")
def admin_time_slots():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM time_slot")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="time_slots")

@app.route("/admin/time_slot/create", methods=["POST"])
@role_required("admin")
def admin_create_time_slot():
    try:
        cursor = db.cursor()
        cursor.callproc("Create_Time_Slot", [
            request.form.get("time_slot_id"),
            request.form.get("day"),
            int(request.form.get("start_hr")),
            int(request.form.get("start_min")),
            int(request.form.get("end_hr")),
            int(request.form.get("end_min"))
        ])
        db.commit()
        cursor.close()
        flash("Time slot created successfully", "secondary")
    except Exception:
        flash("Error creating time slot", "secondary")
    return redirect(url_for("admin_time_slots"))

@app.route("/admin/time_slot/update", methods=["POST"])
@role_required("admin")
def admin_update_time_slot():
    try:
        cursor = db.cursor()
        cursor.callproc("Update_Time_Slot", [
            request.form.get("time_slot_id"),
            request.form.get("day"),
            int(request.form.get("start_hr")),
            int(request.form.get("start_min")),
            int(request.form.get("end_hr")),
            int(request.form.get("end_min"))
        ])
        db.commit()
        cursor.close()
        flash("Time slot updated successfully", "secondary")
    except Exception:
        flash("Error updating time slot", "secondary")
    return redirect(url_for("admin_time_slots"))

@app.route("/admin/time_slot/delete", methods=["POST"])
@role_required("admin")
def admin_delete_time_slot():
    try:
        cursor = db.cursor()
        cursor.callproc("Delete_Time_Slot", [request.form.get("time_slot_id")])
        db.commit()
        cursor.close()
        flash("Time slot deleted successfully", "secondary")
    except Exception:
        flash("Error deleting time slot", "secondary")
    return redirect(url_for("admin_time_slots"))

@app.route("/admin/sections")
@role_required("admin")
def admin_sections():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM section")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="sections")

@app.route("/admin/section/create", methods=["POST"])
@role_required("admin")
def admin_create_section():
    try:
        cursor = db.cursor()
        cursor.callproc("Create_Section", [
            request.form.get("course_id"),
            request.form.get("sec_id"),
            request.form.get("semester"),
            int(request.form.get("sec_year")),
            request.form.get("building"),
            request.form.get("room_number"),
            request.form.get("time_slot_id")
        ])
        db.commit()
        cursor.close()
        flash("Section created successfully", "secondary")
    except Exception:
        flash("Error creating section", "secondary")
    return redirect(url_for("admin_sections"))

@app.route("/admin/section/update", methods=["POST"])
@role_required("admin")
def admin_update_section():
    try:
        cursor = db.cursor()
        cursor.callproc("Update_Section", [
            request.form.get("course_id"),
            request.form.get("sec_id"),
            request.form.get("semester"),
            int(request.form.get("sec_year")),
            request.form.get("building"),
            request.form.get("room_number"),
            request.form.get("time_slot_id")
        ])
        db.commit()
        cursor.close()
        flash("Section updated successfully", "secondary")
    except Exception:
        flash("Error updating section", "secondary")
    return redirect(url_for("admin_sections"))

@app.route("/admin/section/delete", methods=["POST"])
@role_required("admin")
def admin_delete_section():
    try:
        cursor = db.cursor()
        cursor.callproc("Delete_Section", [
            request.form.get("course_id"),
            request.form.get("sec_id"),
            request.form.get("semester"),
            int(request.form.get("sec_year"))
        ])
        db.commit()
        cursor.close()
        flash("Section deleted successfully", "secondary")
    except Exception:
        flash("Error deleting section", "secondary")
    return redirect(url_for("admin_sections"))

@app.route("/admin/assign_teacher", methods=["POST"])
@role_required("admin")
def admin_assign_teacher():
    try:
        cursor = db.cursor()
        cursor.callproc("Assign_Teacher", [
            request.form.get("instructor_id"),
            request.form.get("course_id"),
            request.form.get("sec_id"),
            request.form.get("semester"),
            int(request.form.get("sec_year"))
        ])
        db.commit()
        cursor.close()
        flash("Teacher assigned successfully", "secondary")
    except Exception:
        flash("Error assigning teacher. Check if section and instructor exist.", "secondary")
    return redirect(url_for("admin_sections"))

@app.route("/admin/remove_teacher", methods=["POST"])
@role_required("admin")
def admin_remove_teacher():
    try:
        cursor = db.cursor()
        cursor.callproc("Remove_Teacher", [
            request.form.get("instructor_id"),
            request.form.get("course_id"),
            request.form.get("sec_id")
        ])
        db.commit()
        cursor.close()
        flash("Teacher removed successfully", "secondary")
    except Exception:
        flash("Error removing teacher", "secondary")
    return redirect(url_for("admin_sections"))

@app.route("/admin/reports", methods=["GET", "POST"])
@role_required("admin")
def admin_reports():
    results = {}
    if request.method == "POST":
        cursor = db.cursor()
        if "dept_avg" in request.form:
            cursor.callproc("Average_Grade_Department", [request.form["dept_name"]])
            results["dept_avg"] = cursor.fetchall()
        elif "class_range" in request.form:
            cursor.callproc("Average_Grade_Range", [
                request.form["course_id"],
                int(request.form["start_year"]),
                int(request.form["end_year"]),
                request.form.get("start_semester") or None,
                request.form.get("end_semester") or None
            ])
            results["class_range"] = cursor.fetchall()
        elif "best_worst" in request.form:
            cursor.callproc("Best_Worst_Sem", [request.form["semester"], int(request.form["year"]), request.form.get("mode", "both")])
            results["best_worst"] = cursor.fetchall()
        elif "tot_students" in request.form:
            cursor.callproc("Tot_Students_Department", [request.form["dept_name"]])
            results["tot_students"] = cursor.fetchall()
        elif "current_enrolled" in request.form:
            cursor.callproc("Current_In_Department", [request.form["dept_name"]])
            results["current_enrolled"] = cursor.fetchall()
        cursor.close()
    return render_template("admin.html", user_id=session["user_id"], page="reports", results=results)

@app.route("/admin/personal", methods=["GET", "POST"])
@role_required("admin")
def admin_personal():
    if request.method == "POST":
        password = request.form.get("password")
        if password:
            p_hash = generate_password_hash(password)
            try:
                cursor = db.cursor()
                cursor.execute("UPDATE user_accounts SET password_hash = %s WHERE user_id = %s", (p_hash, session["user_id"]))
                db.commit()
                cursor.close()
                flash("Password updated successfully", "secondary")
            except Exception:
                flash("Error updating password", "secondary")
        return redirect(url_for("admin_personal"))
    return render_template("admin.html", user_id=session["user_id"], page="personal")

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
    return render_template("instructor.html", user_id=session["user_id"], data=data, page="roster", course_id=course_id, sec_id=sec_id, semester=semester, sec_year=sec_year)

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
    except Exception:
        flash("Error removing student", "secondary")
    return redirect(url_for("instructor_roster", course_id=course_id, sec_id=sec_id, semester=semester, sec_year=sec_year))

@app.route("/instructor/add_advisor", methods=["POST"])
@role_required("instructor")
def instructor_add_advisor():
    student_id = request.form.get("student_id")
    instructor_id = session["user_id"]
    try:
        cursor = db.cursor()
        cursor.callproc("Add_Advisor", [student_id, instructor_id])
        db.commit()
        cursor.close()
        flash("Student added as advisee successfully", "secondary")
    except Exception:
        flash("Error adding advisee", "secondary")
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
        flash("Student removed from advising successfully", "secondary")
    except Exception:
        flash("Error removing advisee", "secondary")
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
    except Exception:
        flash("Error adding prerequisite", "secondary")
    return redirect(url_for("instructor_prereqs"))

@app.route("/instructor/remove_prereq", methods=["POST"])
@role_required("instructor")
def instructor_remove_prereq():
    try:
        cursor = db.cursor()
        cursor.callproc("Remove_Prereq", [request.form.get("course_id"), request.form.get("prereq_id")])
        db.commit()
        cursor.close()
        flash("Prerequisite removed successfully", "secondary")
    except Exception:
        flash("Error removing prerequisite", "secondary")
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
        except Exception:
            flash("Error enrolling in section", "secondary")
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
    except Exception:
        flash("Error dropping course", "secondary")
        return redirect(url_for("student_courses"))

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

if __name__ == "__main__":
    app.run(port=4500)
