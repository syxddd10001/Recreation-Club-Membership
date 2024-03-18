#if you import external modules, also make sure to put it in requirements.txt
import sys
import re
import os

from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   jsonify)
from flask_cors import CORS
import json


ERROR = ""
blacklist = ['--','"',"'", ';'] # list of invalid characters
LOGGED_USER = None

app = Flask(__name__)
CORS(app)

"""Route methods"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if login_server():
            return jsonify({'success': 'true', 'username':LOGGED_USER[0]})
        else:
            return jsonify({'error': ERROR})
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if not LOGGED_USER:
        return redirect('/login')
    return render_template('home.html')



"""Server methods"""

def login_server() -> bool:
    """Login method
        Checks if the user login is valid                 
        
        Arguments: None

        Returns True if the user logs in successfully
        Returns ERROR message otherwise
    """
    
    global ERROR
    global LOGGED_USER
    LOGGED_USER = None
    user = request.json.get('uName')
    password = request.json.get('password')
    # member_type = request.json.get['member_type']


    # checking for bad input
    for char in blacklist:
        if char in user or char in password: 
            ERROR="Bad username or password provided"
            return False

    userdata = read_users('regulars')
    
    if check_user(userdata, user, password):
        LOGGED_USER = (user, 'regular')
        return True
    
    return False

def logout_server():
    global LOGGED_USER
    LOGGED_USER = None

def check_user(userdata : dict, username: str, password: str) -> bool:
    """Check user method
        Checks if an user with the username and password exist                
        
        Arguments: userdata (dictionary), username (string), password (string)

        Returns True if the user username and combination exist
        Returns False otherwise
    """
    for k, v in userdata.items():
        if v['username'] == username and v['password'] == password:
            return True


def read_users(type :str) -> dict:  
    """Read user data
        Reads user data from ./data/*.json files                 
        
        Arguments: member type (string)
        Valid arguments: members, regulars, treasurers, coaches, groups
        

        Returns the user data if data is found
        Returns error if not found
    """
    file_data = None
    result_dict = {}
    json_files = [f for f in os.listdir("data") if f.endswith('.json')]


    file_path = os.path.join("data", type+'.json')
    try:
        with open(file_path, 'r') as file:
            file_data = json.load(file)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"No such file: {0}.json".format(type))


    if file_data is not None:
 
        for item in file_data:
            result_dict.update(item)
    
    return result_dict
    
    


#main function
if __name__ == "__main__":
    app.run()