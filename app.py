from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
import config

# Setting up Flask app
app = Flask(__name__)
app.debug = True
app.secret_key = "secret_key"

# Connecting the database
db = config.dbserver


# Home page → go to login
@app.route("/")
def index():
    return redirect(url_for("login"))


# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""

    if request.method == "GET":
        return render_template("login.html", msg=msg)

    if request.method == "POST":
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


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Admin Page
@app.route("/admin")
def admin():
    if "loggedin" in session and session["role"] == "admin":
        return render_template("admin.html", user_id=session["user_id"])
    return redirect(url_for("login"))


# Instructor Page
@app.route("/instructor")
def instructor():
    if "loggedin" in session and session["role"] == "instructor":
        return render_template("instructor.html", user_id=session["user_id"])
    return redirect(url_for("login"))


# Student Page
@app.route("/student")
def student():
    if "loggedin" in session and session["role"] == "student":
        return render_template("student.html", user_id=session["user_id"])
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(port=4500)