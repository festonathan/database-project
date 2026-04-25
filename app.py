from flask import Flask, render_template, request
#import config

# Connecting the database
db = 0
#config.dbserver

# Setting up Flask app
app = Flask(__name__)
app.debug = True

# The Home page
@app.route("/")
def index():
   return render_template("index.html")

if (__name__ == "__main__"):
   #current port number was choosen arbitrarily
   #and should be changed if causing errors or a more secure method is available
   app.run(port=4500)