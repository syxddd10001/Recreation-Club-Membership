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
from werkzeug.security import generate_password_hash, check_password_hash
sys.path.append("./models")
from users import Member

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
    if request.method == 'POST':
        if signup_server():
            return jsonify({'success': 'true'})
        else:
            return jsonify({'error': ERROR})
    
    return render_template('signup.html')


@app.route('/home', methods=['GET', 'POST'])
def home():
    if not LOGGED_USER:
        return redirect('/login')
    if(request.method == 'GET' or request.method == 'POST'):
        if LOGGED_USER:
            if LOGGED_USER[1] == 'members':
                return render_template('home.html', userInfo=LOGGED_USER)
            elif LOGGED_USER[1] == 'treasurers':
                return render_template('home_treasurers.html', userInfo=LOGGED_USER)
            elif LOGGED_USER[1] == 'coaches':
                return render_template('home_coaches.html', userInfo=LOGGED_USER)
        else:
            return redirect('/login')
        
        


"""Server methods"""

def login_server() -> bool:
    """Login method
        Checks if the user login is valid                 
        
        Arguments: None

        Returns True if the user logs in successfully
        Returns False otherwise
    """
    
    global ERROR
    global LOGGED_USER
    LOGGED_USER = None
    user = request.json.get('uName')
    password = request.json.get('password')
    user_type = request.json.get('userType')

    

    # checking for bad input
    for char in blacklist:
        if char in user or char in password:
            ERROR="Bad username or password provided"
            return False

    if check_user(user, password, user_type):
        LOGGED_USER = (user, user_type)
        return True
    else:
         ERROR = "Invalid username or password"
         return False

def logout_server():
    global LOGGED_USER
    LOGGED_USER = None

def signup_server() -> bool:
    """Signup method
        Signs up a new user              
        
        Arguments: None

        Returns True if the user signup was successful
        Returns False otherwise
    """
    global ERROR
    global LOGGED_USER
    LOGGED_USER = None

    user = request.json.get('uName')
    password = request.json.get('password')
    name = request.json.get('name')
    user_type = request.json.get('userType')


    if user == "" or password == "" or name == "":
        return False

    for char in blacklist:
        if char in user or char in password or char in name: 
            ERROR="Bad name, username or password provided"
            return False

    hashedpassword = generate_password_hash( password, method='scrypt' )

    return write_users(user, name, hashedpassword, user_type)

def check_user(username: str, password: str, user_type: str) -> bool:
    """Check user method
        Checks if an user with the username and password exist in userdata               
        
        Arguments: username (string), password (string), user_type (string)

        Returns True if the user username and combination exist
        Returns False otherwise
    """
    userdata = read_users(user_type)
    for val in userdata.values():
        if val['username'] == username and check_password_hash( val['password'], password ):
            return True
        
    return False

def write_users(username :str, name :str, password :str, user_type :str) -> bool:
    """Writes user data to file
        Write user data to ./data/*.json files                 
        
        Arguments: username, password, member type (strings)

        Returns True if the write was successful
        Returns False otherwise
    """
    try:
        with open(os.path.join('data', user_type+'.json'), 'r') as f:
            userdata = json.load(f)
    except FileNotFoundError:
        userdata = []
    
    if check_user(username, password, user_type):
        global ERROR
        ERROR = "Username already exists"
        return False
    

    new_id = (str(len(userdata) + 1)) 
    new_user = { new_id : {   
                    "username":username, 
                    "name":name,
                    "password":password,
                    "type":"monthly",
                    "schedule": []
                    } 
                }
    
    userdata.append(new_user)
    with open(os.path.join('data', user_type+'.json'), 'w') as f:
        json.dump(userdata, f, indent=4)

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
    app.run(debug=True)