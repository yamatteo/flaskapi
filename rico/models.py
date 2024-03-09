import random
import uuid
from typing import List

from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

S = db.session


class Game(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(8), default="open", nullable=False)

    users: Mapped[List["User"]] = relationship()

    def __repr__(self):
        return f"<Game: {self.name}>"

    @staticmethod
    def generate_random_name():
        # List of plausible South American town names
        towns = [
            "Villarrica",
            "Valparaíso",
            "Santa Cruz",
            "Punta Arenas",
            "Potosí",
            "Maracaibo",
            "Guayaquil",
            "Cuenca",
            "Cuzco",
            "Bariloche",
            "Cartagena",
            "Mendoza",
            "Córdoba",
            "Salta",
            "Ushuaia",
            "Iquitos",
            "Arequipa",
            "Trujillo",
            "Chiclayo",
            "Huaraz",
            "Isla Margarita",
            "Puerto La Cruz",
            "Puerto Cabello",
            "Merida",
            "San Cristóbal",
            "Quito",
            "Guayaquil",
            "Cuenca",
            "Loja",
            "Machala",
            "Manta",
            "San José",
            "Antigua",
            "San Salvador",
            "Tegucigalpa",
            "Managua",
            "Ciudad de Panamá",
            "Cancún",
            "Mérida",
        ]

        # List of country names from South America
        countries = [
            "Argentina",
            "Bolivia",
            "Brasil",
            "Chile",
            "Colombia",
            "Ecuador",
            "Guyana",
            "Paraguay",
            "Perú",
            "Uruguay",
            "Venezuela",
            "Costa Rica",
            "El Salvador",
            "Guatemala",
            "Honduras",
            "Nicaragua",
            "Panamá",
            "México",
        ]
        random_year = random.randint(1578, 1624)
        random_town = random.choice(towns)
        random_country = random.choice(countries)

        return f"{random_town}, {random_country}, {random_year} A.D."

    @classmethod
    def browse(cls, name=None, status=None):
        items = S.query(cls)
        if name:
            items = items.filter(cls.name == name)
        if status:
            items = items.filter(cls.status == status)
        return items.all()

    @classmethod
    def add(cls) -> "Game":
        name = None
        while name is None:
            name = cls.generate_random_name()
            prev_game = S.query(cls).filter(cls.name == name).first()
            if prev_game is not None:
                name = None
        game = cls(name=name)
        S.add(game)
        S.commit()
        S.refresh(game)
        return game


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    password: Mapped[str] = mapped_column(String(80), nullable=False)
    token: Mapped[str] = mapped_column(String(16), nullable=False)

    game_id: Mapped[int] = mapped_column(ForeignKey("game.id"))

    @property
    def game(self):
        return Game.query.get(self.game_id)

    def __repr__(self):
        return f"User[{self.id}]({self.name}, ***, ***, {self.game_id})"

    @classmethod
    def add(cls, name: str, password: str, game_id: int) -> "User":

        user = cls(
            name=name,
            password=password,
            token=uuid.uuid4().hex.upper()[:16],
            game_id=game_id,
        )
        S.add(user)
        S.commit()
        S.refresh(user)
        return user

    def get_id(self):
        return str(self.id)


# class Problem(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     short = db.Column(db.String(80))
#     text = db.Column(db.Text(), nullable=False)

#     def __repr__(self):
#         return f"<Problem: {self.id}>"


# class DueSolution(db.Model):
#     user_id: Mapped[int] = mapped_column(db.ForeignKey("user.id"), primary_key=True)
#     problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), primary_key=True)
#     date = db.Column(db.DateTime, nullable=False)


# class DueComparison(db.Model):
#     user_id: Mapped[int] = mapped_column(db.ForeignKey("user.id"), primary_key=True)
#     problem_id: Mapped[int] = mapped_column(db.ForeignKey("problem.id"), primary_key=True)
#     date = db.Column(db.DateTime, nullable=False)
#     others = db.Column(db.String(20))


# # class DueProblem(db.Model):
# #     id = db.Column(db.Integer, primary_key=True)
# #     due_date = db.Column(db.DateTime, nullable=False)
# #     problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False)
# #     problem = db.relationship("Problem", backref=db.backref("due_problems", lazy=True))
# #     group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
# #     group = db.relationship("Group", backref=db.backref("due_problems", lazy=True))

# #     def __repr__(self):
# #         return f"<DueProblem: {self.group.name} #{self.problem_id} by {self.due_date}>"


# class Solution(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
#     problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False)
#     solution_text = db.Column(db.Text, nullable=False)
#     user = db.relationship("User", backref=db.backref("solutions", lazy=True))
#     problem = db.relationship("Problem", backref=db.backref("solutions", lazy=True))


# # class CompareRequest(db.Model):
# #     id = db.Column(db.Integer, primary_key=True)
# #     due_date = db.Column(db.DateTime, nullable=False)
# #     group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
# #     problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False)


# class Comparison(db.Model):
#     id = db.Column(db.Integer, primary_key=True)

#     user_id: Mapped[int] = mapped_column(db.ForeignKey("user.id"), nullable=False)
#     user: Mapped["User"] = db.relationship(foreign_keys=[user_id])

#     better: Mapped[int] = mapped_column(db.ForeignKey("user.id"), nullable=False)
#     better_user: Mapped["User"] = db.relationship(foreign_keys=[better])

#     worse: Mapped[int] = mapped_column(db.ForeignKey("user.id"), nullable=False)
#     worse_user: Mapped["User"] = db.relationship(foreign_keys=[worse])

#     problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False)

#     motivation = db.Column(db.Text, nullable=False)

#     @property
#     def better_solution(self):
#         return S.query(Solution).filter_by(problem_id=self.problem_id, user_id=self.better).first()

#     @property
#     def worse_solution(self):
#         return S.query(Solution).filter_by(problem_id=self.problem_id, user_id=self.worse).first()


# ### BREAD utilities


# ## Group
# def browse_groups():
#     return S.query(Group).all()


# def read_group(arg):
#     if isinstance(arg, Group):
#         return arg
#     g = S.get(Group, arg) or S.query(Group).filter(Group.name == arg).first()
#     return g


# def edit_group(id, name, extra_users=[]):
#     g = S.get(Group, id)

#     g.name = name
#     g.users = list(set(g.users) | set(extra_users))
#     S.commit()


# def add_group(name):
#     g = S.query(Group).filter(Group.name == name).first()
#     if g is None:
#         g = Group(name=name)
#         S.add(g)
#         S.commit()
#     else:
#         warn(f"Group {name} already exists.")
#     return g


# def delete_group(id=None, *, name=None):
#     if id:
#         g = S.get(Group, id)
#     elif name:
#         g = S.query(Group).filter(Group.name == name).first()
#     else:
#         g = None

#     if g is None:
#         warn(f"Such group (id={id}, name={name}) does not exist.")
#     else:
#         S.delete(g)
#         S.commit()


# ## User
# def browse_users():
#     return S.query(User).all()


# def read_user(arg):
#     if isinstance(arg, User):
#         return arg
#     u = S.get(User, arg) or S.query(User).filter(User.name == arg).first()
#     return u


# def edit_user(id, name, password=...):
#     u = S.get(User, id)
#     u.name = name
#     if password is not ...:
#         u.password = password
#     S.commit()


# def add_user(name, password=None):
#     u = S.query(User).filter(User.name == name).first()
#     if u is None:
#         u = User(name=name, password=password, token=uuid.uuid4().hex.upper()[:16])
#         S.add(u)
#         S.commit()
#     else:
#         warn(f"User {name} already exists.")
#     return u


# def delete_user(id=None, name=None):
#     if id:
#         u = S.get(User, id)
#     elif name:
#         u = S.query(User).filter(User.name == name).first()
#     else:
#         u = None

#     if u is None:
#         warn(f"No such user with id={id} or name={name}")
#     else:
#         S.delete(u)
#         S.commit()

# ## Problem
# def browse_problems():
#     return S.query(Problem).all()

# def read_problem(arg):
#     if isinstance(arg, Problem):
#         return arg
#     p = S.get(Problem, arg) or S.query(Problem).filter(Problem.short == arg).first() or S.query(Problem).filter(Problem.text == arg).first()
#     return p

# def edit_problem(id, short, text):
#     p = S.get(Problem, id)
#     p.short = short
#     p.text = text
#     S.commit()

# def add_problem(short, text):
#     p = S.query(Problem).filter(Problem.short == short).first()
#     if p is None:
#         p = Problem(short=short, text=text)
#         S.add(p)
#         S.commit()
#     else:
#         warn(f"Problem {short} already exists")
#     return p

# def delete_problem(id=None, short=None):
#     if id:
#         p = S.get(Problem, id)
#     elif short:
#         p = S.query(Problem).filter(Problem.short == short).first()
#     else:
#         p = None

#     if p is None:
#         warn(f"No such problem with id={id} or short={short}")
#     else:
#         S.delete(p)
#         S.commit()

# ## Solution
# def browse_solutions():
#     return S.query(Solution).all()

# def read_solution(arg=None):
#     raise NotImplementedError
#     if isinstance(arg, Solution):
#         return arg
#     if isinstance(arg, int):
#         s = S.get(Solution, arg)
#     elif isinstance(arg, tuple[int, int]):
#         user_id, problem_id = arg
#         s = S.query(Solution).filter_by(user_id=user_id, problem_id=problem_id).first()
#     return s

# def edit_solution(id, user_id, problem_id, solution_text):
#     raise NotImplementedError
#     s = S.get(Solution, id)
#     s.user_id = user_id
#     s.problem_id = problem_id
#     s.solution_text = solution_text
#     S.commit()

# def add_solution(user, problem, solution_text):
#     user = read_user(user)
#     problem = read_problem(problem)

#     s = S.query(Solution).filter_by(user_id=user.id, problem_id=problem.id).first()

#     if not s:
#         s = Solution(user_id=user.id, problem_id=problem.id, solution_text=solution_text)
#         S.add(s)
#     else:
#         raise IndexError
#     S.commit()
#     return s

# def delete_solution(id):
#     raise NotImplementedError
#     s = S.get(Solution, id)
#     if s is None:
#         warn(f"No solution with id {id}")
#     else:
#         S.delete(s)
#         S.commit()

# ## Comparisons
#         ## Comparison
# def browse_comparisons():
#     return S.query(Comparison).all()

# def read_comparison(id):
#     return S.get(Comparison, id)

# def edit_comparison(id, user_id, problem_id, better_id, worse_id, motivation):
#     raise NotImplementedError
#     c = read_comparison(id)
#     c.user_id = user_id
#     c.problem_id = problem_id
#     c.better_id = better_id
#     c.worse_id = worse_id
#     c.motivation = motivation
#     S.commit()

# def add_comparison(user, problem, better, worse, motivation):
#     user = read_user(user)
#     problem = read_problem(problem)
#     better = read_user(better)
#     worse = read_user(worse)

#     assert all(x is not None for x in [user, problem, better, worse])
#     assert motivation

#     c = S.query(Comparison).filter_by(user_id=user.id, problem_id=problem.id).first()

#     if c:
#         c.better = better
#         c.worse = worse
#         c.motivation = motivation
#     else:
#         c = Comparison(
#             user_id=user.id,
#             problem_id=problem.id,
#             better=better.id,
#             worse=worse.id,
#             motivation=motivation
#         )
#         S.add(c)
#     S.commit()
#     return c

# def delete_comparison(id):
#     raise NotImplementedError
#     c = read_comparison(id)
#     if c:
#         S.delete(c)
#         S.commit()
#     else:
#         warn(f"No comparison with id {id}")

# ## Relationships

# def set_membership(user, group, value=True):
#     user = read_user(user)
#     group = read_group(group)
#     if value and (not user in group.users):
#         group.users.append(user)
#     elif (not value) and (user in group.users):
#         group.users = [ u for u in group.users if u != user ]
#     S.commit()

# def set_due_solution(group, problem, date, set_to=True):
#     users = read_group(group).users
#     problem = read_problem(problem)
#     for user in users:
#         due = S.query(DueSolution).filter_by(user_id=user.id, problem_id=problem.id).first()
#         if set_to is True and due is None:
#             due = DueSolution(user_id=user.id, problem_id=problem.id, date=date)
#             S.add(due)
#         elif set_to is True and due is not None:
#             due.date = date
#         elif set_to is False and due is not None:
#             S.delete(due)
#     S.commit()

# def _set_due_comparison(user, user1, user2, problem, date, set_to, force):
#     due = S.query(DueSolution).filter(
#         DueSolution.user_id == user.id,
#         DueSolution.problem_id == problem.id,
#         DueSolution.date < datetime.now()
#     ).first()

#     if not due:
#         warn("Should not compare solutions that are not past due.")
#         return

#     due = S.query(DueComparison).filter(
#         DueComparison.user_id == user.id,
#         DueComparison.problem_id == problem.id
#     ).first()
#     others = f"{user1.id};{user2.id}"

#     if due is None and set_to is True:
#         due = DueComparison(user_id=user.id, others=others, problem_id=problem.id, date=date)
#         S.add(due)
#     elif due is not None and set_to is True and force is True:
#         due.date = date
#         due.others = others
#     elif due is not None and set_to is False:
#         S.delete(due)
#     S.commit()

# def set_due_comparison(group=None, problem=None, date=None, set_to=True, force=False):
#     if group is None:
#         for g in S.query(Group).all():
#             set_due_comparison(g, problem, date, set_to)
#         return
#     if problem is None:
#         for due in S.query(DueSolution).filter(
#             DueSolution.date < datetime.now(),
#             DueSolution.date > datetime.now() - timedelta(days=14)
#         ):
#             problem = S.get(Problem, due.problem_id)
#             set_due_comparison(group, due.problem_id, date, set_to)
#         return
#     if date is None:
#         date = datetime.now() + timedelta(days=7)
#     users = list(read_group(group).users)
#     problem = read_problem(problem)
#     random.shuffle(users)
#     for i, user in enumerate(users):
#         _set_due_comparison(user, users[i-1], users[i-2], problem, date, set_to, force)
