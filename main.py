#if you import external modules, also make sure to put it in requirements.txt
import sys
import re
import os
from datetime import datetime 
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
from users import User, Member, Coach, Treasurer, Classes, Transaction

ERROR = ""
blacklist = ['--','"',"'", ';'] # list of invalid characters
LOGGED_USER = None
ALL_CLASSES = []
ALL_TRANSACTIONS = []
ALL_MEMBERS = []

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
    
    update_user_data('members')
    update_user_data('coaches')
    update_user_data('treasurers')
    
    if(request.method == 'GET' or request.method == 'POST'):
        if LOGGED_USER:
            u_type = LOGGED_USER.__dict__['user_type']
            classes = read_users('classes')
            transactions = read_users('transactions')
            global ALL_CLASSES
            ALL_CLASSES = []
            
            global ALL_TRANSACTIONS
            ALL_TRANSACTIONS = []
            
            for c in classes.values():
                ALL_CLASSES.append(dict_to_class(c))           

            if LOGGED_USER.user_type == "treasurers":
                for t in transactions.values():
                    ALL_TRANSACTIONS.append(dict_to_class(t))


            if u_type == 'members':
                upcoming_classes = classes_signed_up_for(LOGGED_USER.upcoming_classes)

                all_classes=set(ALL_CLASSES)-set(upcoming_classes)

                return render_template('home.html', userInfo=LOGGED_USER, allClasses=all_classes, upcomingClasses=upcoming_classes) #return all classes as well
            
            elif u_type == 'treasurers':
                return render_template('home_treasurers.html', userInfo=LOGGED_USER, allClasses=ALL_CLASSES, allTransactions=ALL_TRANSACTIONS)#return all classes as well
            
            elif u_type == 'coaches':
                upcoming_classes = classes_signed_up_for(LOGGED_USER.upcoming_classes)

                all_classes=set(ALL_CLASSES)-set(upcoming_classes)
 
                return render_template('home_coaches.html', userInfo=LOGGED_USER, allClasses=ALL_CLASSES, upcomingClasses=upcoming_classes) #return all classes as well
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
    
    update_user_data('members')
    
    common_classes = classes_signed_up_for(LOGGED_USER.finished_classes + LOGGED_USER.upcoming_classes)
    unpaid_classes = classes_signed_up_for(find_in_dict(LOGGED_USER.finished_classes + LOGGED_USER.upcoming_classes, "payment_status", "unpaid"))
    paid_classes = classes_signed_up_for(find_in_dict(LOGGED_USER.finished_classes + LOGGED_USER.upcoming_classes, "payment_status", "paid"))

    return render_template('payment.html', userInfo=LOGGED_USER, classInfo=ALL_CLASSES, signedupClasses=common_classes, unpaidClasses=unpaid_classes, paidClasses=paid_classes)
 
@app.route('/payclass', methods=['GET', 'POST'])
def payclass():
    if not LOGGED_USER:
        return redirect('login')

    if request.method == 'POST':
        if not validate_credit_card():
            return jsonify({'error':'true', 'message':'Payment unsuccessful, enter valid information'})

        if pay_class_server():
            print("successfully paid")
            
            return jsonify({'success':'true', 'message':'Payment was successful!'})
        else:
            return jsonify({'error':'true', 'message':'Payment unsuccessful'})

@app.route('/signupclass', methods=['GET', 'POST'])
def signupclass():
    if not LOGGED_USER:
        return redirect('login')
    
    if request.method == 'POST':
        if signup_class_server('members'):
            return jsonify({'success':'true'})
        else:
            return jsonify({'error':'true'})
        
#@app.route('/get_class', methods=['GET', 'POST'])
#def signupclass():
#    return True

@app.route('/class.html', methods=['GET', 'POST'])
def class_page():
    update_user_data('members')
    update_user_data('coaches')
    update_user_data('treasurers')
    class_id = request.args.get('id')
    specific_class = get_class_by_id(class_id)    
    user_id = request.args.get('user_id')
    #user_type = request.args.get('user_type')
    user = find_user(user_id, 'members')
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('name')
        message = data.get('message')
        class_id = data.get('class_id')
        specific_class = get_class_by_id(class_id)    
        specific_class.add_message((username, message))
        update_json_file('classes', class_id, 'messages', (username, message), True)
    return render_template('class.html', Class=specific_class, userInfo=user)

@app.route('/statements', methods=['GET', 'POST'])
def statements():
    if not LOGGED_USER:
        return redirect('login')
    
    if not LOGGED_USER.user_type == 'treasurers':
        ERROR = 'You must be logged in as a treasurer to perform this action!'
        return jsonify({'error':ERROR})

    revenues = get_transactions("revenue")
    expenses = get_transactions("expense")
    return render_template('statements.html', allRevenues=revenues, allExpenses=expenses)

@app.route('/members', methods=['GET', 'POST'])
def members():
    if not LOGGED_USER:
        return redirect('login')
    
    global ALL_MEMBERS
    ALL_MEMBERS = read_users("members").values()

    global ALL_CLASSES
    ALL_CLASSES = read_users("classes").values()

    attended = [] # [[], []]
    not_attended = []
    for c in ALL_CLASSES:
        x = get_members(c["id"])
        attended.append(x[1])
        not_attended.append(x[2])

    return render_template('members.html',
                           allMembers=ALL_MEMBERS,
                           allClasses=ALL_CLASSES,
                           attendedClasses=attended,
                           notAttendedClasses=not_attended) ## return list of all members


@app.route('/createclass', methods=['POST', 'POST'])
def createclass():
    if not LOGGED_USER:
        return redirect('login')
    
    if request.method == 'POST':
        if create_class_server():
            return jsonify({'success':'true'})
        else:
            return jsonify({'error':'true', 'message':'something went wrong :/'})


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

    # hashedpassword = generate_password_hash( password, method='scrypt' )

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
        ERROR = "Name, username or password cannot be empty"
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

def get_class_by_id(class_id):
    """Find class method
        Checks if a class is linked to specific class_id in classes.json               
        
        Arguments: class_id (string)

        Returns the class if found
        Returns False otherwise
    """
    return read_classes(class_id) # Why does this function exist haha



def update_user_data(user_type):
    """Update user data method
        Updates user data by rereading it               
        
        Arguments: user_type (string)

        Returns True if the update was successful
        Returns False otherwise
    """ 
    global LOGGED_USER
    userdata = read_users(user_type)
    if not LOGGED_USER:
        return False
    
    for val in userdata.values():
        if val['username'] == LOGGED_USER.username:
            
            LOGGED_USER = dict_to_class(val)
            return True
        
    return False

def update_all():
    classes = read_users('classes')
    transactions = read_users('transactions')

    global ALL_CLASSES
    ALL_CLASSES = []
    
    global ALL_TRANSACTIONS
    ALL_TRANSACTIONS = []
    
    for c in classes.values():
        ALL_CLASSES.append(dict_to_class(c)) 

    if LOGGED_USER.user_type == "treasurers":
        for t in transactions.values():
            ALL_TRANSACTIONS.append(dict_to_class(t))

    return True and update_user_data(LOGGED_USER.user_type)
    
    

def write_users(uName :str, FLname :str, passw :str, utype :str, finished_classes=[], upcoming_classes=[]) -> bool:
    """Writes user data to file
        Write user data to ./data/(members|treasurers|coaches).json files                 
        
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
    new_id = (str(len(userdata) + 1)) 
    if utype == 'members':
        user = Member(id=new_id,
                      username=uName,
                      name=FLname,
                      password=passw,
                      user_type=utype,
                      member_type='regular',
                      finished_classes=[],
                      upcoming_classes=[],
                      monthly_sub_count=0,
                      consecutive_attendance=0)

    if utype == 'coaches':
        user = Coach(id=new_id,
                      username=uName,
                      name=FLname,
                      password=passw,
                      user_type=utype,
                      finished_classes=[],
                      upcoming_classes=[])


    if utype == 'treasurers':
        user = Treasurer(id=new_id,
                          username=uName,
                          name=FLname,
                          password=passw,
                          user_type=utype,
                          ) 

    
    new_user = { new_id : user.__dict__ }
    
    userdata.append(new_user)
    with open(os.path.join('data', utype+'.json'), 'w') as f:
        json.dump(userdata, f, indent=4)

    return True

def write_classes(admin, members, coach, date, time, utype='classes') -> bool:
    """Writes classes data to file
        Write classes data to ./data/classes.json files                 
        
        Arguments: id, admin, members, coach date, time, utype (strings)
        Optional arguments: finished_classes, upcoming_classes

        Returns True if the write was successful
        Returns False otherwise
    """
    try:
        with open(os.path.join('data', utype+'.json'), 'r') as f:
            userdata = json.load(f)
    
    except FileNotFoundError:
        userdata = []
    obj = None
    new_id = (str(len(userdata) + 1)) 
    if utype == 'classes':
        obj = Classes(id=new_id,
                    admin=admin,
                    members=members,
                    coach=coach,
                    date=date,
                    time=time,
                    user_type=utype)
         

    
    new_obj = { new_id : obj.__dict__ }
    userdata.append(new_obj)
    
    with open(os.path.join('data', utype+'.json'), 'w') as f:
        json.dump(userdata, f, indent=4)
    
    return True

def find_user(user_id: str, type: any) -> User:
    """ Find a user object
        Arguments: user_id (string)

        Returns user if found
        Returns None if not
    """
    type = "members" # temporary
    file_data = None
    file_path = os.path.join("data", type+'.json')
    try:
        with open(file_path, 'r') as file:
            file_data = json.load(file)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"No such file: {0}.json".format(type))
        return None
    
    if file_data is not None:
        for item in file_data:
            user_data = list(item.values())[0] 
            if 'id' in user_data and user_data['id'] == user_id:
                return Member(**user_data)

    return None


def write_transactions(title, status, transaction_type, amount, date, date_due, utype="transactions") -> bool:
    """Writes transaction data to file
        Write transaction data to ./data/*.json files                 
        
        Arguments: title, status, transaction_type, amount (float), date, date_due (strings)

        Returns True if the write was successful
        Returns False otherwise
    """
    try:
        with open(os.path.join('data', utype+'.json'), 'r') as f:
            userdata = json.load(f)
    
    except FileNotFoundError:
        userdata = []

    obj = None
    new_id = (str(len(userdata) + 1)) 

    if utype == 'transactions':
        obj = Transaction(id=new_id,
                          title=title, 
                          status=status,
                          user_type=utype,
                          amount=amount,
                          transaction_type=transaction_type,
                          date=date,
                          date_due=date_due)

    new_obj = { new_id : obj.__dict__ }
    userdata.append(new_obj)
    
    with open(os.path.join('data', utype+'.json'), 'w') as f:
        json.dump(userdata, f, indent=4)

    return True

def read_users(type :str) -> dict: 
    """Read user data
        Reads user data from ./data/*.json files                 
        
        Arguments: member type (string)
        Valid arguments: members, regulars, treasurers, coaches, classes
        

        Returns the user data if data is found
        Returns an empty dictionary and prints error if not found
    """
    file_data = None
    result_dict = {}
    #json_files = [f for f in os.listdir("data") if f.endswith('.json')]


    file_path = os.path.join("data", type+'.json')
    try:
        with open(file_path, 'r') as file:
            file_data = json.load(file)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"No such file: {0}.json".format(type))
        return result_dict

    if file_data is not None:
        for item in file_data:
            result_dict.update(item)

    return result_dict

def read_classes(class_id: str) -> Classes:
    """Read class data
        Arguments: class_id (string)

        Returns class if found
        Returns None if not
    """
    file_data = None
    file_path = os.path.join("data", 'classes.json')
    try:
        with open(file_path, 'r') as file:
            file_data = json.load(file)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"No such file: classes.json")
        return None

    if file_data is not None:
        for item in file_data:
            class_data = list(item.values())[0]  # Get the class details dictionary
            if 'id' in class_data and class_data['id'] == class_id:
                return Classes(**class_data)

    return None


def dict_to_class(user :dict) -> Member | Coach | Treasurer | Classes | Transaction | None:
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
        return_user = Member(id=user["id"],
                            username=user["username"],
                            name=user["name"], 
                            password=user["password"], 
                            finished_classes=user["finished_classes"],
                            upcoming_classes=user["upcoming_classes"],
                            member_type=user["member_type"],
                            user_type=user["user_type"],
                            monthly_sub_count=user["monthly_sub_count"],
                            consecutive_attendance=user["consecutive_attendance"])    

    elif u_type == "coaches":
        return_user = Coach(id=user["id"],
                            username=user["username"],
                            name=user["name"],
                            password=user["password"],
                            user_type=user["user_type"],
                            finished_classes=user["finished_classes"],
                            upcoming_classes=user["upcoming_classes"])

    elif u_type == "treasurers":
        return_user = Treasurer(id=user["id"],
                                username=user["username"],
                                name=user["name"],
                                password=user["password"],
                                user_type=user["user_type"]
                                )
    
    elif u_type == "classes":    
        return_user = Classes(id=user["id"],
                              admin=user["admin"],
                              members=user["members"],
                              coach=user["coach"],
                              date=user["date"],
                              time=user["time"],
                              user_type=user["user_type"])
        

    elif u_type == "transactions":
        return_user = Transaction(id=user["id"],
                              title=user["title"],
                              status=user["status"],
                              user_type=user["user_type"],
                              transaction_type=user["transaction_type"],
                              amount=user["amount"],
                              date=user["date"],
                              date_due=user["date_due"])

    return return_user

def update_json_file(file: str, update_id :any, update_field :any, update_value: any, addTo=False):
    """update_json_file method
        Updates json fields with the values provided
        
        Arguments: update_id, update_field, update_value (str)
        
        Returns True if update was successful
        Returns False otherwise
    """
    
    file_path = os.path.join("data", file+'.json')
    success = False

    with open(file_path, "r") as jsonFile:
        data = json.load(jsonFile)   
    
    for item in data:
        if (item.get(update_id)):
            
            if addTo:
                item[update_id][update_field].append(update_value)
            else:
                item[update_id][update_field]=update_value
            success = True
            break
    
    if not success:
        return False   

    with open(file_path, "w") as jsonFile:
        json.dump(data, jsonFile, indent=4)
    
    return True

def find_in_dict(local_list, field, parameter) -> list:
    """Find in dict method
        Searches the local_list (list of dictionaries) and finds the values of field that match the paramter 
        
        Arguments: local_list (list of dictionaries), field (string), parameter (string)

        Returns the list of found items
    """    
    found = []
    for class_dict in local_list:
        if str(class_dict[field]) == str(parameter):  
            found.append(class_dict) 
    
    return found

def pay_class_server():
    """Pay for class method
        Finds the class being paid for and then updates paid status for that class for member

        Arguments: None

        Returns True if payment was successful
        Returns False otherwise
    """
    
    class_id = request.json.get('class_id') # get the class id which is to be paid
    all_local_classes = LOGGED_USER.finished_classes + LOGGED_USER.upcoming_classes
    # get all current users classes 

    payment_for = find_in_dict(all_local_classes, "class_id", class_id)
    # finding the class from the users class list

    new_list = []
    new_obj = None

    for cl in LOGGED_USER.upcoming_classes: # this basically goes through all the users classes and updates the status to paid
        if cl == payment_for[0]:
            new_obj = {'class_id':payment_for[0]['class_id'], "payment_status":"paid"}
            new_list.append(new_obj)

            continue 
        new_list.append(cl)

    if new_list != LOGGED_USER.upcoming_classes: # if there was a change in the list, i.e if any of the class' status was changed
        return (update_json_file('members', LOGGED_USER.id, 'upcoming_classes', new_list)
                and
                write_transactions(title=f"payment from {LOGGED_USER.username} for class {new_obj['class_id']}", 
                                status="paid", 
                                transaction_type="revenue", 
                                amount=10, 
                                date=datetime.now().strftime("%m/%d/%Y"), 
                                date_due=datetime.now().strftime("%m/%d/%Y")))
        
        # return if the update was successful

    new_list = []
    for cl in LOGGED_USER.finished_classes: #same as above but with finished classes
        if cl == payment_for[0]:
            new_obj = {'class_id':payment_for[0]['class_id'], "payment_status":"paid"}
            new_list.append(new_obj)
            continue
        
        new_list.append(cl)

    if set(new_list) != set(LOGGED_USER.finished_classes):   
        return (update_json_file('members', LOGGED_USER.id, 'finished_classes', new_list) 
                and
                write_transactions(title=f"payment from {LOGGED_USER.username} for class {new_obj['class_id']}", 
                                    status="paid", 
                                    transaction_type="revenue", 
                                    amount=10, 
                                    date=datetime.now().strftime("%m/%d/%Y"), 
                                    date_due=datetime.now().strftime("%m/%d/%Y")))

        
    return False
        

def classes_signed_up_for(target_list):
    """Classes signed up for method
        Finds the intersection of classes between the target list and the all the classes in the database
        
        Arguments: target_list (list of class references)

        Returns the list of common classes as a list of Classes objects 
    """ # target list would be for example -- { 'class_id':'1', 'payment':'unpaid'} ie its a reference not an class data
    common_classes = []
    for class_in_all in ALL_CLASSES:

        for class_in_target in target_list:
            if str(class_in_all.id) == str(list(class_in_target.values())[0]):
                common_classes.append(class_in_all)
    
    return common_classes # common_classes would be [{CLASSES Data type 1} ... {CLASSES Data type n}]

def signup_class_server(user_type):
    class_id = request.json.get('class_id')

    LOGGED_USER.add_upcoming_class({"class_id":class_id, "payment_status":"unpaid"})

    update_json_file(user_type, LOGGED_USER.id, "upcoming_classes", LOGGED_USER.upcoming_classes)

    for cl in ALL_CLASSES:
        if class_id == cl.id:
            cl.add_member({"id":LOGGED_USER.id, "username":LOGGED_USER.username, "name":LOGGED_USER.name})

            update_json_file('classes', cl.id, "members", cl.members)
            return True
        
    return False

def finish_class_server():
    class_id = request.json.get('class_id')

    LOGGED_USER.add_finished_class({"class_id":class_id, "payment_status":"paid"})

    return update_json_file('members', LOGGED_USER.id, "finished_classes", LOGGED_USER.finished_classes)

def validate_credit_card()->bool:
    cc_num = request.json.get('cardnumber') # 1234-5678-5678-5678 or 1234 5678 5678 5678
    exp = request.json.get('expdate') # 2024-03-20
    cvv = request.json.get('cvv') # 123

    if cc_num == None or exp == None or cvv == None:
        return False
    
    cc_num = ''.join(c for c in cc_num if c.isdigit()) # converting from 1234-5678-5678-5678 to 1234567856785678

    today = datetime.today().date() # todays date 
    #from datetime import datetime for this

    exp = datetime.strptime(str(exp), "%Y-%m-%d").date()
    #convert this to datetime format for comparison

    if len(cc_num) != 16:
        return False
       
    if exp < today:
        return False

    if len(cvv) != 3:  
        return False  

    return True

def get_transactions(transaction_type) -> list:
    """get expenses function
        Gets a list of all the revenues or incomes from transactions.json
        
        Arguments: transaction_type (string)

        Returns a list of Transaction objects
    """
    transactions = []
    data = read_users("transactions")
    if data is None:
        return transactions
    
    for rx in data.values():
        if rx["transaction_type"] == transaction_type:
            transactions.append(dict_to_class(rx))

    return transactions


def get_unpaid_expenses(transaction_type, status) -> list:
    """get expenses function
        Gets a list of all the unpaid expenses from transactions.json
        
        Arguments: transaction_type, status (string) # status = paid/unpaid

        Returns a list of unpaid Transaction objects sorted by date
    """
    unpaid_transactions = []
    data = read_users("transactions")

    for ut in data.values():
        if ut["transaction_type"] == transaction_type and ut["status"] == "unpaid":
            unpaid_transactions.append(dict_to_class(ut))
    
    return unpaid_transactions

def get_accounts_payables(transaction_type, status) -> list:
    """get expenses function
        Gets a list of all the payments that were made in advance from transactions.json
        
        Arguments: transaction_type (string), status # status = paid/unpaid

        Returns a list of unpaid Transaction objects sorted by date
    """
    pass
    

def get_members(c_id) -> list:
    """get members function
        Gets a list of all the members

        Returns a list of Member objects
    """
    ALL_MEMBERS = read_users("members")
    classes_data = read_users("classes")

    attended = []
    not_attended = []

    class_members = []

    for cls in classes_data.values():
        if cls["id"] == c_id:
            for member in cls["members"]:
                class_members.append(dict_to_class(ALL_MEMBERS[member["id"]]))

    for id, member_info in ALL_MEMBERS.items():
        for c in member_info['finished_classes']:
            if c['id'] == c_id:
                attended.append(dict_to_class(member_info))

        for c in member_info['upcoming_classes']:
            if c['class_id'] == c_id:
                not_attended.append(dict_to_class(member_info))

    return class_members, attended, not_attended
    
    """
    members = []
    all_members = read_users("members")
    
    for member in all_members.values():
        members.append(dict_to_class(member))

    return members 
    """

def create_class_server()->bool:
    username = request.json.get('username')
    date = request.json.get('date')
    time = request.json.get('time')
    user_type = request.json.get('user_type')

    if (username == "" or date == "" or time == "" or user_type == ""):
        return False

    if not (is_valid_date(date) and is_valid_time(time)):
        return False
    
    if user_type == 'coaches':
        write_classes(admin=username, members=[], coach=username, date=date, time=int(time))
        update_all()

        update_json_file(user_type, LOGGED_USER.id, "upcoming_classes", LOGGED_USER.upcoming_classes)

        write_transactions(title=f"payment to coach {LOGGED_USER.username} for class {len(ALL_CLASSES)}",
                           status="unpaid", 
                           transaction_type="expense",
                           amount=250,
                           date=datetime.now().date().strftime("%m/%d/%Y"),
                           date_due=date)
        update_all()
        return True
    
    if user_type == 'treasurers':
        pass

    return False

def is_valid_date(date_string):
    regex = r"^(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/(19|20)\d{2}$"
    match = re.match(regex, date_string)
    return bool(match)

def is_valid_time(time_string):
    regex = r"^([01][0-9]|2[0-3])[0-5][0-9]$" 
    match = re.match(regex, time_string)
    return bool(match)


#main function
if __name__ == "__main__":
    #print(get_members("1"))
    app.run(debug=True)