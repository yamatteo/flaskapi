from flask import Blueprint, render_template, request, redirect, url_for
from ..models import add_user, read_group, add_group, edit_group, delete_group, browse_groups, read_user

bp = Blueprint('admin', __name__, url_prefix="/88EB109E/")

@bp.route('/groups/')
def groups_index():
    groups = browse_groups()
    return render_template('admin/groups/browse.html', groups=groups)

@bp.route('/groups/new/', methods=['GET', 'POST'])  
def new_group():
    if request.method == 'POST':
        name = request.form['name']
        group = add_group(name)
        return redirect(url_for('.groups_index'))

    return render_template('admin/groups/add.html')

@bp.route('/groups/<int:id>/')
def view_group(id):
    group = read_group(id)
    return render_template('admin/groups/read.html', group=group)

@bp.route('/groups/<int:id>/edit/', methods=['GET', 'POST'])
def update_group(id):
    group = read_group(id)
    
    if request.method == 'POST':
        name = request.form['name']
        new_user_name = request.form["new_user_name"]
        new_user = read_user(new_user_name)
        if new_user_name and not new_user:
            new_user = add_user(new_user_name)
        if new_user:
            edit_group(id, name, extra_users=[new_user])
        else:
            edit_group(id, name)
        return redirect(url_for('.update_group', id=id))

    return render_template('admin/groups/edit.html', group=group)

@bp.route('/groups/<int:id>/delete/', methods=['POST'])  
def delete_group(id):
    delete_group(id)
    return redirect(url_for('.groups_index'))


## Users

@bp.route('/users/<int:id>/')
def view_user(id):
    user = read_group(id)
    return render_template('admin/users/read.html', user=user)