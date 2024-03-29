import json
class User: 
    def __init__(self, username, name, password, user_type):
        self.username = username
        self.name = name
        self.password = password
        self.user_type = user_type


class Member(User):
    def __init__(self, username, name, password, finished_classes=[], upcoming_classes=[], user_type='members', member_type='regular', monthly_sub_count=0, consecutive_attendance=0):
        super().__init__(username, name, password, user_type)
        self.member_type=member_type
        self.finished_classes=finished_classes
        self.upcoming_classes=upcoming_classes
        self.monthly_sub_count=monthly_sub_count
        self.consecutive_attendance=consecutive_attendance
    
    def add_class(self, date_time):
        self.upcoming_classes.append(date_time)
      
    
    def get_classes(self):
        past = self.finished_classes
        future = self.upcoming_classes
        return past.append(future)

    def change_member_type(self, update_type):
        if update_type != 'regular' or update_type != 'monthly':
            return False
        
        self.member_type=update_type
        return True

    def increment_attendance(self):
        self.consecutive_attendance += 1
    
    def increment_monthly_sub_count(self):
        self.monthly_sub_count += 1

    def to_json(self):
        return json.dumps(self.__dict__)
    

class Coach(User):
    def __init__(self, username, name, password, finished_classes=[], upcoming_classes=[], user_type='coaches'):
        super().__init__(username, name, password, user_type)
        self.finished_classes=finished_classes
        self.upcoming_classes=upcoming_classes

    

class Treasurer(User):
    def __init__(self, username, name, password, user_type='treasurers', expenses=[], revenues=[]):
        super().__init__(username, name, password, user_type)

class Classes:
    def __init__(self, admin, coach, date, time, members=[]):
        self.admin = admin
        self.coach = coach
        self.date = date
        self.time = time
        self.members = members
    
    def add_member(self, member):
        self.members.append(member)
    
    def get_members(self):
        return self.members
    
    def to_json(self):
        return json.dumps(self.__dict__)


class Transaction:
    def __init__(self, id, amount=0):
        self.id = id
        self.amount = amount

class Expense(Transaction):
    def __init__(self, id, amount, expense_type):
        super().__init__(id, amount)
        self.expense_type = expense_type

    def increment_amount(self, inc_amount):
        self.amount += inc_amount

class Income(Transaction):
    def __init__(self, id, amount, income_type):
        super().__init__(id, amount)
        self.expense_type = income_type

    def increment_amount(self, inc_amount):
        self.amount += inc_amount