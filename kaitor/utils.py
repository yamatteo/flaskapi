from datetime import datetime
import hashlib
import struct
from types import SimpleNamespace
import uuid

from rich import print

from app import DueProblem, Group, Membership, Problem, Solution, User, app, db

S = db.session

def as_dict(obj):
    return { key:value for key, value in vars(obj).items() if key[0]!='_' }

def namespace(obj):
    return SimpleNamespace(**as_dict(obj))

# Groups
def browse_group():
    with app.app_context():
        return [ namespace(g) for g in S.query(Group).all() ]
    
def add_group(name):
    with app.app_context():
        g = S.query(Group).filter_by(name=name).first()

        if g is None:
            g = Group(name=name)
            S.add(g)
            S.commit()
        
        return namespace(S.query(Group).filter_by(name=name).first())

def delete_group(name):
    with app.app_context():
        g = S.query(Group).filter_by(name=name).first()

        if g is not None:
            S.delete(g)
            S.commit()

# Users
def browse_user():
    with app.app_context():
        return [ namespace(u) for u in S.query(User).all() ]

def read_user(username):
    with app.app_context():
        u = S.query(User).filter_by(name=username).first()
        return None if u is None else namespace(u)

def edit_user(username, password=...):
    with app.app_context():
        u = S.query(User).filter_by(name=username).first()

        if u is None:
            raise IndexError(f"No user with name {username}.")

        if password is not ...:
            u.password = password

        S.commit()



def add_user(username):
    with app.app_context():
        u = S.query(User).filter_by(name=username).first()            

        if u is None:
            token = uuid.uuid4().hex.upper()
            u = User(name=username, token=token)
            S.add(u)
            S.commit()
        
        return namespace(S.query(User).filter_by(name=username).first())


def delete_user(username):
    with app.app_context():
        u = S.query(User).filter_by(name=username).first()
        
        if u is not None:
            S.delete(u)
            S.commit()
    

def reset_password(username, password=None):
    with app.app_context():
        u = S.query(User).filter_by(name=username).first()

        if u is None:
            raise IndexError(f"No user names {username}")

        u.password = password
        if password is None:
            u.token = uuid.uuid4().hex.upper()

        S.commit()

# Memberships
def browse_membership():
    with app.app_context():
        # print(S.query(Membership).all())
        return S.query(Membership).all()

def get_members(group):
    with app.app_context():
        memberships = S.query(Membership).filter_by(group=group)
        users = [
            S.get(User, m.user_id) for m in memberships
        ]
        return users


def add_membership(groupname, username):
    with app.app_context():
        u = S.query(User).filter_by(name=username).first()
        g = S.query(Group).filter_by(name=groupname).first()
        m = S.query(Membership).filter_by(user_id=u.id, group_id=g.id).first()

        if m is None:
            m = Membership(group_id=g.id, user_id=u.id)
            S.add(m)
            S.commit()
        
        return namespace(S.query(Membership).filter_by(user_id=u.id, group_id=g.id).first())

def remove_membership(group, username):
    with app.app_context():
        u = S.query(User).filter_by(name=username).first()
        m = S.query(Membership).filter_by(group=group, user_id=u.id).first()

        if m is not None:
            S.delete(m)
            S.commit()
            
# Problems
def read_problem(text):
    with app.app_context():
        p = S.query(Problem).filter_by(text=text).first()

        if p:
            return namespace(p)
        else:
            return None


def add_problem(text):
    with app.app_context():
        p = S.query(Problem).filter_by(text=text).first()
        
        if p is None:
            p = Problem(text=text)
            S.add(p)
            S.commit()

        return namespace(S.query(Problem).filter_by(text=text).first())

def edit_problem(id, text, due_date=None):
    with app.app_context():
        problem = db.session.get(Problem, id)
        if due_date is None:
            due_date = problem.due_date
        problem.text=text
        problem.due_date=due_date
        db.session.commit()

# DueProblems
def add_due_problem(due_date, problem_id, group_id):
    with app.app_context():
        dp = S.query(DueProblem).filter_by(problem_id=problem_id, group_id=group_id).first()

        if dp is None:
            dp = DueProblem(due_date=due_date, problem_id=problem_id, group_id=group_id)

            S.add(dp)
            S.commit()

        return namespace(S.query(DueProblem).filter_by(problem_id=problem_id, group_id=group_id).first())


# Solutions
def add_solution(user_id, problem_id, solution_text):
    with app.app_context():
        solution = S.query(Solution).filter_by(user_id=user_id, problem_id=problem_id).first()

        if solution is None:
            solution = Solution(user_id=user_id, problem_id=problem_id, solution_text=solution_text)

            S.add(solution)
        else:
            solution.solution_text = solution_text
        S.commit()

        return namespace(S.query(Solution).filter_by(user_id=user_id, problem_id=problem_id).first())

def delete_solution(user_id, problem_id):
    with app.app_context():
        solution = S.query(Solution).filter_by(user_id=user_id, problem_id=problem_id).first()

        if solution is not None:
            S.delete(solution)
        S.commit()
        

    