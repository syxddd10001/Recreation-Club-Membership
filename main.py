#if you import external modules, also make sure to put it in requirements.txt
import sys
import re

from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   jsonify)
from flask_cors import CORS

ERROR = ""
blacklist = ['--','"',"'", ';'] # list of invalid characters
LOGGED_USER = None

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if login_server():
            return jsonify({'success': True})
        else:
            return jsonify({'error': False})
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')


def login_server():
    """Login method
        Checks if the user login is valid                 
        
        Arguments: None

        Return True if the user logs in successfully
        Returns ERROR message otherwise
    """
    
    global ERROR
    
    user = request.json.get('uName')
    password = request.json.get('password')
    # member_type = request.json.get['member_type']

    print(request.data)
    # checking for bad input
    for char in blacklist:
        if char in user or char in password: 
            ERROR="Bad username or password provided"
            return ERROR

    # TEMPLATE
    if user != "admin" or password != "password":
        ERROR = "username or password is incorrect"
        return False


    global LOGGED_USER
    LOGGED_USER = (user, "admin")


    return True




#main function
if __name__ == "__main__":
    app.run()