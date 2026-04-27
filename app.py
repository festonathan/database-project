from flask import Flask, render_template, request
#import config

# Connecting the database
db = 0
#config.dbserver

# Setting up Flask app
app = Flask(__name__)
app.debug = True

# The Home Page
@app.route("/")
def index():
   return render_template("index.html")

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
   if (request.method == "GET"):
      return render_template("login.html")
   if (request.method == "POST"):
      # Pulls user input from the html page
      username = request.form['username']
      user_password = request.form['password']

      print(username)
      print(user_password)
      # Renders different Pages depending on user permissions
      if ("admin" and False):
         return render_template("admin_page.html")
      elif ("instructor" and False):
         return render_template("instructor_page.html")
      elif ("student" and False):
         return render_template("student_page.html")
      # If User not present in database, sends them back to login page
      else:
         return render_template("login.html")

if (__name__ == "__main__"):
   #current port number was choosen arbitrarily
   #and should be changed if causing errors or a more secure method is available
   app.run(port=4500)