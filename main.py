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
from users import User, Member, Coach, Treasurer, Classes

ERROR = ""
blacklist = ['--','"',"'", ';'] # list of invalid characters
LOGGED_USER = None
ALL_CLASSES = []

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
            return jsonify({'success': 'true', 'username':LOGGED_USER.__dict__.get('username')})
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
            u_type = LOGGED_USER.__dict__['user_type']
            classes = read_users('classes')
            global ALL_CLASSES
            ALL_CLASSES = []

            for c in classes.values():
                ALL_CLASSES.append(dict_to_class(c))
            

            if u_type == 'members':
                return render_template('home.html', userInfo=LOGGED_USER, allClasses=ALL_CLASSES) #return all classes as well
            elif u_type == 'treasurers':
                return render_template('home_treasurers.html', userInfo=LOGGED_USER, allClasses=ALL_CLASSES)#return all classes as well
            elif u_type == 'coaches':
                return render_template('home_coaches.html', userInfo=LOGGED_USER, allClasses=ALL_CLASSES) #return all classes as well
        else:
            return redirect('/login')
        
@app.route('/all_classes', methods=['GET', 'POST'])
def all_classes():
    if not LOGGED_USER:
        return redirect('/login')
    
    if (request.method == 'GET'):
        classes = read_users('classes').values()
        cl_list = []
        for c in classes:
            cl_list.append(dict_to_class(c).__dict__)

        
        return jsonify({'success':'true', 'data':cl_list})

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if LOGGED_USER is None:
        return redirect('login')

    return render_template('payment.html', userInfo=LOGGED_USER, allClasses=ALL_CLASSES)

@app.route('/paidclass', methods=['GET', 'POST'])
def payclass():
    if not LOGGED_USER:
        return redirect('login')

    if request.method == 'POST':
        if pay_class_server():
            jsonify({'success':'true'})


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
            global LOGGED_USER
            LOGGED_USER = dict_to_class(val)
            return True
        
    return False

def write_users(uName :str, FLname :str, passw :str, utype :str, finished_classes=[], upcoming_classes=[]) -> bool:
    """Writes user data to file
        Write user data to ./data/*.json files                 
        
        Arguments: username, password, member type (strings)
        Optional arguments: finished_classes, upcoming_classes

        Returns True if the write was successful
        Returns False otherwise
    """
    try:
        with open(os.path.join('data', utype+'.json'), 'r') as f:
            userdata = json.load(f)
    except FileNotFoundError:
        userdata = []
    
    if check_user(uName, passw, utype):
        global ERROR
        ERROR = "Username already exists"
        return False
    user = None
    if utype == 'members':
        user = Member(username=uName,
                      name=FLname,
                      password=passw,
                      user_type=utype,
                      member_type='regular',
                      finished_classes=[],
                      upcoming_classes=[],
                      monthly_sub_count=0,
                      consecutive_attendance=0)

    if utype == 'coaches':
        user = Coach(username=uName,
                      name=FLname,
                      password=passw,
                      user_type=utype,
                      finished_classes=[],
                      upcoming_classes=[])


    new_id = (str(len(userdata) + 1)) 
    new_user = { new_id : user.__dict__ }
    
    userdata.append(new_user)
    with open(os.path.join('data', utype+'.json'), 'w') as f:
        json.dump(userdata, f, indent=4)

    return True

def read_users(type :str) -> User: 
    """Read user data
        Reads user data from ./data/*.json files                 
        
        Arguments: member type (string)
        Valid arguments: members, regulars, treasurers, coaches, classes
        

        Returns the user data if data is found
        Returns an empty dictionary and prints error if not found
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

def dict_to_class(user :dict) -> Member | Coach | Treasurer | Classes | None:
    """Dict to User Class 
        Converts a dictionary to user class               
        
        Arguments: user (dict)
        Valid arguments: members, regulars, treasurers, coaches, classes
        
 
        Returns Member, Coach or Treasurer class
        Returns None if 
    """
    if type(user) is not dict:
        return None
    
    u_type = user.get("user_type")
    
    return_user = None
    if u_type == "members": 
        return_user = Member(username=user["username"],
                        name=user["name"], 
                        password=user["password"], 
                        finished_classes=user["finished_classes"],
                        upcoming_classes=user["upcoming_classes"],
                        member_type=user["member_type"],
                        user_type=user["user_type"],
                        monthly_sub_count=user["monthly_sub_count"],
                        consecutive_attendance=user["consecutive_attendance"])    

    elif u_type == "coaches":
        return_user = Coach(username=user["username"],
                      name=user["name"],
                      password=user["password"],
                      user_type=user["user_type"],
                      finished_classes=user["finished_classes"],
                      upcoming_classes=user["upcoming_classes"])

    elif u_type == "classes":    
        return_user = Classes(id=user["class_id"],
                              admin=user["admin"],
                              members=user["members"],
                              coach=user["coach"],
                              date=user["date"],
                              time=user["time"],
                              user_type=user["user_type"])
        


    return return_user

def update_json_file(file: str, update_id, update_field, update_value):
    file_path = os.path.join("data", file+'.json')
    with open(file_path, "r") as jsonFile:
        data = json.load(jsonFile)
    
    for item in data:
        if (item.get(update_id)):
            item[update_id][update_field]=update_value
            break
    
    with open(file_path, "w") as jsonFile:
        json.dump(data, jsonFile, indent=4)
    


def pay_class_server():
    class_id = request.json.get('class_id')
    all_local_classes = LOGGED_USER.finished_classes + LOGGED_USER.upcoming_classes
    #all_local_classes = list of dictionaries ie [{LOCAL_CLASS DATA TYPE}] 
    
    payment_for = next(c for c in all_local_classes if c["class_id"] == class_id)
          
        
    return False

#main function
if __name__ == "__main__":
    app.run(debug=True)