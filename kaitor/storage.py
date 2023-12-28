import yaml
from models import Group, User, db, memberships, S


def export_members(path):
    groups = {group.id: group.name for group in S.query(Group).all()}
    users = {
        user.id: {
            "name": user.name,
            "password": user.password,
            "points": user.points,
            "token": user.token,
        }
        for user in S.query(User).all()
    }
    members = {
        group.name: [user.name for user in group.users]
        for group in S.query(Group).all()
    }
    with open(path, "w") as f:
        f.write(yaml.dump({"members": members, "groups": groups, "users": users}))


def import_members(path, drop=False):
    with open(path, "r") as f:
        data = yaml.safe_load(f.read())

    if drop:
        Group.__table__.drop(db.engine)
        User.__table__.drop(db.engine)
        memberships.drop(db.engine)
        db.create_all()

    groups = data["groups"]
    for id, name in groups.items():
        group_name = Group(id=id, name=name)
        S.add(group_name)
        S.commit()
    reverse_group = { name: id for id, name in groups.items() }

    users = data["users"]
    for id, user in users.items():
        u = User(id=id, **user)
        S.add(u)
        S.commit()
    reverse_user = { user["name"]: id for id, user in users.items() }

    members = data["members"]
    for group_name, member_names in members.items():
        group = S.get(Group, reverse_group[group_name])

        group.users = [ S.get(User, reverse_user[name]) for name in member_names ]
        S.commit()
