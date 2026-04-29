from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
import config

app = Flask(__name__)
app.secret_key = "secret_key"
db = config.dbserver


def get_cursor():
    db.ping(reconnect=True)
    return db.cursor()


def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "loggedin" not in session or session.get("role") != required_role:
                flash("Access denied. Please log in with the correct role.", "secondary")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        cursor = get_cursor()
        cursor.callproc("Check_Login", [username])
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


# =========================
# ADMIN
# =========================

@app.route("/admin")
@role_required("admin")
def admin():
    return render_template("admin.html", user_id=session["user_id"])


@app.route("/admin/courses")
@role_required("admin")
def admin_courses():
    cursor = get_cursor()
    cursor.execute("SELECT * FROM course ORDER BY course_id")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="courses")


@app.route("/admin/course/create", methods=["POST"])
@role_required("admin")
def admin_create_course():
    try:
        cursor = get_cursor()
        cursor.callproc("Create_Course", [
            request.form.get("course_id"),
            request.form.get("title"),
            request.form.get("dept_name"),
            int(request.form.get("credits"))
        ])
        db.commit()
        cursor.close()
        flash("Course created successfully.", "secondary")
    except Exception as e:
        flash(f"Error creating course: {e}", "secondary")
    return redirect(url_for("admin_courses"))


@app.route("/admin/course/update", methods=["POST"])
@role_required("admin")
def admin_update_course():
    try:
        cursor = get_cursor()
        cursor.callproc("Update_Course", [
            request.form.get("course_id"),
            request.form.get("title"),
            request.form.get("dept_name"),
            int(request.form.get("credits"))
        ])
        db.commit()
        cursor.close()
        flash("Course updated successfully.", "secondary")
    except Exception as e:
        flash(f"Error updating course: {e}", "secondary")
    return redirect(url_for("admin_courses"))


@app.route("/admin/course/delete", methods=["POST"])
@role_required("admin")
def admin_delete_course():
    try:
        cursor = get_cursor()
        cursor.callproc("Delete_Course", [request.form.get("course_id")])
        db.commit()
        cursor.close()
        flash("Course deleted successfully.", "secondary")
    except Exception as e:
        flash(f"Error deleting course: {e}", "secondary")
    return redirect(url_for("admin_courses"))


@app.route("/admin/students")
@role_required("admin")
def admin_students():
    cursor = get_cursor()

    cursor.execute("""
        SELECT student_id, first_name, middle_name, last_name, dept_name, tot_cred, advisor_id
        FROM student
        ORDER BY last_name, first_name
    """)
    data = cursor.fetchall()

    cursor.execute("SELECT dept_name FROM department ORDER BY dept_name")
    departments = cursor.fetchall()

    cursor.execute("""
        SELECT instructor_id, first_name, middle_name, last_name
        FROM instructor
        ORDER BY last_name, first_name
    """)
    instructors = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin.html",
        user_id=session["user_id"],
        data=data,
        page="students",
        departments=departments,
        instructors=instructors
    )

@app.route("/admin/student/create", methods=["POST"])
@role_required("admin")
def admin_create_student():
    try:
        p_hash = generate_password_hash(request.form.get("password"))

        cursor = get_cursor()
        cursor.callproc("Create_Student", [
            request.form.get("student_id"),
            request.form.get("first_name"),
            request.form.get("middle_name") or "",
            request.form.get("last_name"),
            request.form.get("dept_name") or None,
            int(request.form.get("tot_cred") or 0),
            request.form.get("advisor_id") or None,
            p_hash
        ])
        db.commit()
        cursor.close()
        flash("Student created successfully.", "secondary")
    except Exception as e:
        flash(f"Error creating student: {e}", "secondary")
    return redirect(url_for("admin_students"))


@app.route("/admin/student/update", methods=["POST"])
@role_required("admin")
def admin_update_student():
    try:
        password = request.form.get("password")
        p_hash = generate_password_hash(password) if password else ""

        cursor = get_cursor()
        cursor.callproc("Update_Student", [
            request.form.get("student_id"),
            request.form.get("first_name"),
            request.form.get("middle_name") or "",
            request.form.get("last_name"),
            request.form.get("dept_name") or None,
            int(request.form.get("tot_cred") or 0),
            request.form.get("advisor_id") or None,
            p_hash
        ])
        db.commit()
        cursor.close()
        flash("Student updated successfully.", "secondary")
    except Exception as e:
        flash(f"Error updating student: {e}", "secondary")
    return redirect(url_for("admin_students"))


@app.route("/admin/student/delete", methods=["POST"])
@role_required("admin")
def admin_delete_student():
    try:
        cursor = get_cursor()
        cursor.callproc("Delete_Student", [request.form.get("student_id")])
        db.commit()
        cursor.close()
        flash("Student deleted successfully.", "secondary")
    except Exception as e:
        flash(f"Error deleting student: {e}", "secondary")
    return redirect(url_for("admin_students"))


@app.route("/admin/instructors")
@role_required("admin")
def admin_instructors():
    cursor = get_cursor()

    cursor.execute("""
        SELECT instructor_id, first_name, middle_name, last_name, dept_name, salary
        FROM instructor
        ORDER BY last_name, first_name
    """)
    data = cursor.fetchall()

    cursor.execute("SELECT dept_name FROM department ORDER BY dept_name")
    departments = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin.html",
        user_id=session["user_id"],
        data=data,
        page="instructors",
        departments=departments
    )


@app.route("/admin/instructor/create", methods=["POST"])
@role_required("admin")
def admin_create_instructor():
    try:
        p_hash = generate_password_hash(request.form.get("password"))

        cursor = get_cursor()
        cursor.callproc("Create_Instructor", [
            request.form.get("instructor_id"),
            request.form.get("first_name"),
            request.form.get("middle_name") or "",
            request.form.get("last_name"),
            request.form.get("dept_name") or None,
            float(request.form.get("salary") or 0),
            p_hash
        ])
        db.commit()
        cursor.close()
        flash("Instructor created successfully.", "secondary")
    except Exception as e:
        flash(f"Error creating instructor: {e}", "secondary")
    return redirect(url_for("admin_instructors"))


@app.route("/admin/instructor/update", methods=["POST"])
@role_required("admin")
def admin_update_instructor():
    try:
        password = request.form.get("password")
        p_hash = generate_password_hash(password) if password else ""

        cursor = get_cursor()
        cursor.callproc("Update_Instructor", [
            request.form.get("instructor_id"),
            request.form.get("first_name"),
            request.form.get("middle_name") or "",
            request.form.get("last_name"),
            request.form.get("dept_name") or None,
            float(request.form.get("salary") or 0),
            p_hash
        ])
        db.commit()
        cursor.close()
        flash("Instructor updated successfully.", "secondary")
    except Exception as e:
        flash(f"Error updating instructor: {e}", "secondary")
    return redirect(url_for("admin_instructors"))


@app.route("/admin/instructor/delete", methods=["POST"])
@role_required("admin")
def admin_delete_instructor():
    try:
        cursor = get_cursor()
        cursor.callproc("Delete_Instructor", [request.form.get("instructor_id")])
        db.commit()
        cursor.close()
        flash("Instructor deleted successfully.", "secondary")
    except Exception as e:
        flash(f"Error deleting instructor: {e}", "secondary")
    return redirect(url_for("admin_instructors"))


@app.route("/admin/classrooms")
@role_required("admin")
def admin_classrooms():
    cursor = get_cursor()
    cursor.execute("SELECT * FROM classroom ORDER BY building, room_number")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="classrooms")


@app.route("/admin/classroom/create", methods=["POST"])
@role_required("admin")
def admin_create_classroom():
    try:
        cursor = get_cursor()
        cursor.callproc("Create_Classroom", [
            request.form.get("building"),
            request.form.get("room_number"),
            int(request.form.get("capacity"))
        ])
        db.commit()
        cursor.close()
        flash("Classroom created successfully.", "secondary")
    except Exception as e:
        flash(f"Error creating classroom: {e}", "secondary")
    return redirect(url_for("admin_classrooms"))


@app.route("/admin/classroom/update", methods=["POST"])
@role_required("admin")
def admin_update_classroom():
    try:
        cursor = get_cursor()
        cursor.callproc("Update_Classroom", [
            request.form.get("building"),
            request.form.get("room_number"),
            int(request.form.get("capacity"))
        ])
        db.commit()
        cursor.close()
        flash("Classroom updated successfully.", "secondary")
    except Exception as e:
        flash(f"Error updating classroom: {e}", "secondary")
    return redirect(url_for("admin_classrooms"))


@app.route("/admin/classroom/delete", methods=["POST"])
@role_required("admin")
def admin_delete_classroom():
    try:
        cursor = get_cursor()
        cursor.callproc("Delete_Classroom", [
            request.form.get("building"),
            request.form.get("room_number")
        ])
        db.commit()
        cursor.close()
        flash("Classroom deleted successfully.", "secondary")
    except Exception as e:
        flash(f"Error deleting classroom: {e}", "secondary")
    return redirect(url_for("admin_classrooms"))


@app.route("/admin/departments")
@role_required("admin")
def admin_departments():
    cursor = get_cursor()
    cursor.execute("SELECT * FROM department ORDER BY dept_name")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="departments")


@app.route("/admin/department/create", methods=["POST"])
@role_required("admin")
def admin_create_department():
    try:
        cursor = get_cursor()
        cursor.callproc("Create_Department", [
            request.form.get("dept_name"),
            request.form.get("building"),
            float(request.form.get("budget") or 0)
        ])
        db.commit()
        cursor.close()
        flash("Department created successfully.", "secondary")
    except Exception as e:
        flash(f"Error creating department: {e}", "secondary")
    return redirect(url_for("admin_departments"))


@app.route("/admin/department/update", methods=["POST"])
@role_required("admin")
def admin_update_department():
    try:
        cursor = get_cursor()
        cursor.callproc("Update_Department", [
            request.form.get("dept_name"),
            request.form.get("building"),
            float(request.form.get("budget") or 0)
        ])
        db.commit()
        cursor.close()
        flash("Department updated successfully.", "secondary")
    except Exception as e:
        flash(f"Error updating department: {e}", "secondary")
    return redirect(url_for("admin_departments"))


@app.route("/admin/department/delete", methods=["POST"])
@role_required("admin")
def admin_delete_department():
    try:
        cursor = get_cursor()
        cursor.callproc("Delete_Department", [request.form.get("dept_name")])
        db.commit()
        cursor.close()
        flash("Department deleted successfully.", "secondary")
    except Exception as e:
        flash(f"Error deleting department: {e}", "secondary")
    return redirect(url_for("admin_departments"))


@app.route("/admin/time_slots")
@role_required("admin")
def admin_time_slots():
    cursor = get_cursor()
    cursor.execute("SELECT * FROM time_slot ORDER BY time_slot_id")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="time_slots")


@app.route("/admin/time_slot/create", methods=["POST"])
@role_required("admin")
def admin_create_time_slot():
    try:
        cursor = get_cursor()
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
        flash("Time slot created successfully.", "secondary")
    except Exception as e:
        flash(f"Error creating time slot: {e}", "secondary")
    return redirect(url_for("admin_time_slots"))


@app.route("/admin/time_slot/update", methods=["POST"])
@role_required("admin")
def admin_update_time_slot():
    try:
        cursor = get_cursor()
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
        flash("Time slot updated successfully.", "secondary")
    except Exception as e:
        flash(f"Error updating time slot: {e}", "secondary")
    return redirect(url_for("admin_time_slots"))


@app.route("/admin/time_slot/delete", methods=["POST"])
@role_required("admin")
def admin_delete_time_slot():
    try:
        cursor = get_cursor()
        cursor.callproc("Delete_Time_Slot", [request.form.get("time_slot_id")])
        db.commit()
        cursor.close()
        flash("Time slot deleted successfully.", "secondary")
    except Exception as e:
        flash(f"Error deleting time slot: {e}", "secondary")
    return redirect(url_for("admin_time_slots"))


@app.route("/admin/sections")
@role_required("admin")
def admin_sections():
    cursor = get_cursor()
    cursor.execute("SELECT * FROM section ORDER BY sec_year DESC, semester, course_id, sec_id")
    data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", user_id=session["user_id"], data=data, page="sections")


@app.route("/admin/section/create", methods=["POST"])
@role_required("admin")
def admin_create_section():
    try:
        cursor = get_cursor()
        cursor.callproc("Create_Section", [
            request.form.get("course_id"),
            request.form.get("sec_id"),
            request.form.get("semester"),
            int(request.form.get("sec_year")),
            request.form.get("building") or None,
            request.form.get("room_number") or None,
            request.form.get("time_slot_id") or None
        ])
        db.commit()
        cursor.close()
        flash("Section created successfully.", "secondary")
    except Exception as e:
        flash(f"Error creating section: {e}", "secondary")
    return redirect(url_for("admin_sections"))


@app.route("/admin/section/update", methods=["POST"])
@role_required("admin")
def admin_update_section():
    try:
        cursor = get_cursor()
        cursor.callproc("Update_Section", [
            request.form.get("course_id"),
            request.form.get("sec_id"),
            request.form.get("semester"),
            int(request.form.get("sec_year")),
            request.form.get("building") or None,
            request.form.get("room_number") or None,
            request.form.get("time_slot_id") or None
        ])
        db.commit()
        cursor.close()
        flash("Section updated successfully.", "secondary")
    except Exception as e:
        flash(f"Error updating section: {e}", "secondary")
    return redirect(url_for("admin_sections"))


@app.route("/admin/section/delete", methods=["POST"])
@role_required("admin")
def admin_delete_section():
    try:
        cursor = get_cursor()
        cursor.callproc("Delete_Section", [
            request.form.get("course_id"),
            request.form.get("sec_id"),
            request.form.get("semester"),
            int(request.form.get("sec_year"))
        ])
        db.commit()
        cursor.close()
        flash("Section deleted successfully.", "secondary")
    except Exception as e:
        flash(f"Error deleting section: {e}", "secondary")
    return redirect(url_for("admin_sections"))


@app.route("/admin/assign_teacher", methods=["POST"])
@role_required("admin")
def admin_assign_teacher():
    try:
        cursor = get_cursor()
        cursor.callproc("Assign_Teacher", [
            request.form.get("instructor_id"),
            request.form.get("course_id"),
            request.form.get("sec_id"),
            request.form.get("semester"),
            int(request.form.get("sec_year"))
        ])
        db.commit()
        cursor.close()
        flash("Teacher assigned successfully.", "secondary")
    except Exception as e:
        flash(f"Error assigning teacher: {e}", "secondary")
    return redirect(url_for("admin_sections"))


@app.route("/admin/remove_teacher", methods=["POST"])
@role_required("admin")
def admin_remove_teacher():
    try:
        cursor = get_cursor()
        cursor.callproc("Remove_Teacher", [
            request.form.get("instructor_id"),
            request.form.get("course_id"),
            request.form.get("sec_id"),
            request.form.get("semester"),
            int(request.form.get("sec_year"))
        ])
        db.commit()
        cursor.close()
        flash("Teacher removed successfully.", "secondary")
    except Exception as e:
        flash(f"Error removing teacher: {e}", "secondary")
    return redirect(url_for("admin_sections"))


@app.route("/admin/reports", methods=["GET", "POST"])
@role_required("admin")
def admin_reports():
    results = {}

    if request.method == "POST":
        cursor = get_cursor()

        try:
            if "dept_avg" in request.form:
                cursor.callproc("Average_Grade_Department", [request.form.get("dept_name")])
                results["dept_avg"] = cursor.fetchall()

            elif "class_range" in request.form:
                cursor.callproc("Average_Grade_Range", [
                    request.form.get("course_id"),
                    int(request.form.get("start_year")),
                    int(request.form.get("end_year"))
                ])
                results["class_range"] = cursor.fetchall()

            elif "best_worst" in request.form:
                cursor.callproc("Best_Worst_Sem", [
                    request.form.get("semester"),
                    int(request.form.get("year")),
                    request.form.get("mode", "both")
                ])

                rows = []
                while True:
                    rows.extend(cursor.fetchall())
                    if not cursor.nextset():
                        break

                results["best_worst"] = rows

            elif "tot_students" in request.form:
                cursor.callproc("Tot_Students_Department", [request.form.get("dept_name")])
                results["tot_students"] = cursor.fetchall()

            elif "current_enrolled" in request.form:
                cursor.callproc("Current_In_Department", [request.form.get("dept_name")])
                results["current_enrolled"] = cursor.fetchall()

        except Exception as e:
            flash(f"Report error: {e}", "secondary")

        cursor.close()

    return render_template("admin.html", user_id=session["user_id"], page="reports", results=results)


@app.route("/admin/personal", methods=["GET", "POST"])
@role_required("admin")
def admin_personal():
    if request.method == "POST":
        password = request.form.get("password")

        if password:
            try:
                p_hash = generate_password_hash(password)
                cursor = get_cursor()
                cursor.execute(
                    "UPDATE user_accounts SET password_hash = %s WHERE user_id = %s",
                    (p_hash, session["user_id"])
                )
                db.commit()
                cursor.close()
                flash("Password updated successfully.", "secondary")
            except Exception as e:
                flash(f"Error updating password: {e}", "secondary")

        return redirect(url_for("admin_personal"))

    return render_template("admin.html", user_id=session["user_id"], page="personal")


# =========================
# INSTRUCTOR
# =========================

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

    cursor = get_cursor()

    if semester and sec_year:
        cursor.callproc("Check_Instructor_Section", [
            instructor_id,
            semester,
            int(sec_year)
        ])
        data = cursor.fetchall()
    else:
        cursor.execute("""
            SELECT t.course_id, c.title, t.sec_id, t.semester, t.sec_year
            FROM teaches t
            JOIN course c ON t.course_id = c.course_id
            WHERE t.instructor_id = %s
            ORDER BY t.sec_year DESC, t.semester, t.course_id, t.sec_id
        """, [instructor_id])
        data = cursor.fetchall()

    cursor.close()

    return render_template(
        "instructor.html",
        user_id=instructor_id,
        data=data,
        page="sections",
        filter_semester=semester,
        filter_year=sec_year
    )


@app.route("/instructor/roster", methods=["GET", "POST"])
@role_required("instructor")
def instructor_roster():
    course_id = request.values.get("course_id")
    sec_id = request.values.get("sec_id")
    semester = request.values.get("semester")
    sec_year = request.values.get("sec_year")
    data = None

    if course_id and sec_id and semester and sec_year:
        cursor = get_cursor()
        cursor.callproc("Check_Section_Roster", [
            course_id,
            sec_id,
            semester,
            int(sec_year)
        ])
        data = cursor.fetchall()
        cursor.close()

    return render_template(
        "instructor.html",
        user_id=session["user_id"],
        data=data,
        page="roster",
        course_id=course_id,
        sec_id=sec_id,
        semester=semester,
        sec_year=sec_year
    )


@app.route("/instructor/submit_grade", methods=["POST"])
@role_required("instructor")
def instructor_submit_grade():
    course_id = request.form.get("course_id")
    sec_id = request.form.get("sec_id")
    semester = request.form.get("semester")
    sec_year = request.form.get("sec_year")

    try:
        cursor = get_cursor()
        cursor.callproc("Submit_Grade", [
            request.form.get("student_id"),
            course_id,
            sec_id,
            semester,
            int(sec_year),
            request.form.get("grade") or None
        ])
        db.commit()
        cursor.close()
        flash("Grade updated.", "secondary")
    except Exception as e:
        flash(f"Error updating grade: {e}", "secondary")

    return redirect(url_for(
        "instructor_roster",
        course_id=course_id,
        sec_id=sec_id,
        semester=semester,
        sec_year=sec_year
    ))


@app.route("/instructor/remove_student", methods=["POST"])
@role_required("instructor")
def instructor_remove_student():
    student_id = request.form.get("student_id")
    course_id = request.form.get("course_id")
    sec_id = request.form.get("sec_id")
    semester = request.form.get("semester")
    sec_year = request.form.get("sec_year")

    try:
        cursor = get_cursor()
        cursor.callproc("Drop_Section", [
            student_id,
            course_id,
            sec_id,
            semester,
            int(sec_year)
        ])
        db.commit()
        cursor.close()
        flash("Student removed from section.", "secondary")
    except Exception as e:
        flash(f"Error removing student: {e}", "secondary")

    return redirect(url_for(
        "instructor_roster",
        course_id=course_id,
        sec_id=sec_id,
        semester=semester,
        sec_year=sec_year
    ))


@app.route("/instructor/advising")
@role_required("instructor")
def instructor_advising():
    instructor_id = session["user_id"]

    cursor = get_cursor()
    cursor.execute("""
        SELECT student_id, first_name, middle_name, last_name, dept_name
        FROM student
        WHERE advisor_id = %s
        ORDER BY last_name, first_name
    """, [instructor_id])
    advisees = cursor.fetchall()
    cursor.close()

    return render_template("instructor.html", user_id=instructor_id, page="advising", advisees=advisees)


@app.route("/instructor/add_advisor", methods=["POST"])
@role_required("instructor")
def instructor_add_advisor():
    try:
        cursor = get_cursor()
        cursor.callproc("Add_Advisor", [
            request.form.get("student_id"),
            session["user_id"]
        ])
        db.commit()
        cursor.close()
        flash("Student added as advisee.", "secondary")
    except Exception as e:
        flash(f"Error adding advisee: {e}", "secondary")

    return redirect(url_for("instructor_advising"))


@app.route("/instructor/remove_advisor", methods=["POST"])
@role_required("instructor")
def instructor_remove_advisor():
    try:
        cursor = get_cursor()
        cursor.callproc("Remove_Advisor", [request.form.get("student_id")])
        db.commit()
        cursor.close()
        flash("Student removed from advising.", "secondary")
    except Exception as e:
        flash(f"Error removing advisee: {e}", "secondary")

    return redirect(url_for("instructor_advising"))


@app.route("/instructor/prereqs")
@role_required("instructor")
def instructor_prereqs():
    cursor = get_cursor()
    cursor.execute("""
        SELECT p.course_id, c.title, p.prereq_id, pc.title
        FROM prereq p
        JOIN course c ON p.course_id = c.course_id
        JOIN course pc ON p.prereq_id = pc.course_id
        ORDER BY p.course_id, p.prereq_id
    """)
    prereqs = cursor.fetchall()
    cursor.close()

    return render_template("instructor.html", user_id=session["user_id"], page="prereqs", prereqs=prereqs)


@app.route("/instructor/add_prereq", methods=["POST"])
@role_required("instructor")
def instructor_add_prereq():
    try:
        cursor = get_cursor()
        cursor.callproc("Add_Prereq", [
            request.form.get("course_id"),
            request.form.get("prereq_id")
        ])
        db.commit()
        cursor.close()
        flash("Prerequisite added successfully.", "secondary")
    except Exception as e:
        flash(f"Error adding prerequisite: {e}", "secondary")

    return redirect(url_for("instructor_prereqs"))


@app.route("/instructor/remove_prereq", methods=["POST"])
@role_required("instructor")
def instructor_remove_prereq():
    try:
        cursor = get_cursor()
        cursor.callproc("Remove_Prereq", [
            request.form.get("course_id"),
            request.form.get("prereq_id")
        ])
        db.commit()
        cursor.close()
        flash("Prerequisite removed successfully.", "secondary")
    except Exception as e:
        flash(f"Error removing prerequisite: {e}", "secondary")

    return redirect(url_for("instructor_prereqs"))


# =========================
# STUDENT
# =========================

@app.route("/student")
@role_required("student")
def student():
    return render_template("student.html", user_id=session["user_id"])


@app.route("/student/courses")
@role_required("student")
def student_courses():
    student_id = session["user_id"]

    cursor = get_cursor()
    cursor.execute("""
        SELECT t.course_id, c.title, t.sec_id, t.semester, t.sec_year, t.grade
        FROM takes t
        JOIN course c ON t.course_id = c.course_id
        WHERE t.student_id = %s
        ORDER BY t.sec_year DESC, t.semester, t.course_id
    """, [student_id])
    data = cursor.fetchall()
    cursor.close()

    return render_template("student.html", user_id=student_id, data=data, page="courses")


@app.route("/student/advisor")
@role_required("student")
def student_advisor():
    student_id = session["user_id"]

    cursor = get_cursor()
    cursor.callproc("Check_Student_Advisor", [student_id])
    data = cursor.fetchall()
    cursor.close()

    return render_template("student.html", user_id=student_id, data=data, page="advisor")


@app.route("/student/enroll", methods=["GET", "POST"])
@role_required("student")
def student_enroll():
    student_id = session["user_id"]

    if request.method == "POST":
        try:
            cursor = get_cursor()
            cursor.callproc("Enroll_Section", [
                student_id,
                request.form.get("course_id"),
                request.form.get("sec_id"),
                request.form.get("semester"),
                int(request.form.get("sec_year"))
            ])
            db.commit()
            cursor.close()
            flash("Enrolled successfully.", "secondary")
            return redirect(url_for("student_courses"))
        except Exception as e:
            flash(f"Error enrolling in section: {e}", "secondary")
            return redirect(url_for("student_enroll"))

    cursor = get_cursor()
    cursor.execute("""
        SELECT s.course_id, c.title, s.sec_id, s.semester, s.sec_year, s.building, s.room_number
        FROM section s
        JOIN course c ON s.course_id = c.course_id
        WHERE (s.course_id, s.sec_id, s.semester, s.sec_year) NOT IN (
            SELECT course_id, sec_id, semester, sec_year
            FROM takes
            WHERE student_id = %s
        )
        ORDER BY s.sec_year DESC, s.semester, s.course_id
        LIMIT 50
    """, [student_id])
    available = cursor.fetchall()
    cursor.close()

    return render_template("student_enroll.html", user_id=student_id, available=available)


@app.route("/student/drop", methods=["POST"])
@role_required("student")
def student_drop():
    student_id = session["user_id"]

    try:
        cursor = get_cursor()
        cursor.callproc("Drop_Section", [
            student_id,
            request.form.get("course_id"),
            request.form.get("sec_id"),
            request.form.get("semester"),
            int(request.form.get("sec_year"))
        ])
        db.commit()
        cursor.close()
        flash("Course dropped.", "secondary")
    except Exception as e:
        flash(f"Error dropping course: {e}", "secondary")

    return redirect(url_for("student_courses"))


if __name__ == "__main__":
    app.run(port=4500, debug=True)