from flask import Blueprint, render_template, request, redirect, url_for
from datetime import date as datetime_date
from ..models import *

bp = Blueprint('admin', __name__, url_prefix="/88EB109E/")

@bp.route('/')
def main():
    groups = browse_groups()
    problems = browse_problems()
    return render_template('admin/main.html', groups=groups, problems=problems)

@bp.route('/set_due_solutions/', methods=['POST'])
def set_due_solutions():
    group_id = request.form['group']
    problem_id = request.form['problem']
    action = request.form['action']
    date=request.form['date']
    d, m, y = map(int, date.split('-'))
    date = datetime_date(y, m, d)
    next = request.args.get('next', url_for('kaitor.admin.main'))

    set_due_solution(group_id, problem_id, date=date, set_to=(action == 'add'))

    return redirect(next)

@bp.route('/set_due_comparisons/', methods=['POST'])
def set_due_comparisons():
    group_id = request.form['group']
    problem_id = request.form['problem']
    action = request.form['action']
    date=request.form['date']
    d, m, y = map(int, date.split('-'))
    date = datetime_date(y, m, d)
    next = request.args.get('next', url_for('kaitor.admin.main'))

    set_due_comparison(group_id, problem_id, date=date, set_to=(action == 'add'))

    return redirect(next)

@bp.route('/groups/')
def groups_index():
    groups = browse_groups()
    return render_template('admin/groups/index.html', groups=groups)

@bp.route('/groups/new/', methods=['GET', 'POST'])  
def new_group():
    if request.method == 'POST':
        name = request.form['name']
        group = add_group(name)
        return redirect(url_for('kaitor.admin.groups_index'))

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
        return redirect(url_for('kaitor.admin.update_group', id=id))

    return render_template('admin/groups/edit.html', group=group)

@bp.route('/groups/<int:id>/delete/', methods=['POST'])  
def delete_group(id):
    delete_group(id)
    return redirect(url_for('kaitor.admin.groups_index'))


## Users
@bp.route('/users/<int:id>/')
def view_user(id):
    user = read_group(id)
    return render_template('admin/users/read.html', user=user)


## Problems
@bp.route('/problems/')
def problems_index():
    problems = browse_problems()
    return render_template('admin/problems/index.html', problems=problems)

@bp.route('/problems/<id>')
def view_problem(id):
    problem = read_problem(id)
    return render_template('admin/problems/read.html', problem=problem)


@bp.route('/problems/new', methods=["GET", "POST"])
def new_problem():
    if request.method == 'POST':
        short = request.form['short']
        text = request.form['text']
        problem = add_problem(short, text)
        return redirect(url_for('kaitor.admin.problems_index'))

    return render_template('admin/problems/new.html')

@bp.route('/problems/<int:id>/edit/', methods=['GET', 'POST'])
def update_problem(id):
    problem = read_problem(id)
    
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
        return redirect(url_for('kaitor.admin.update_group', id=id))

    return render_template('admin/problems/edit.html', problem=problem)



@bp.route('/problems/<int:id>/delete/', methods=['POST'])  
def delete_problem(id):
    delete_problem(id)
    return redirect(url_for('kaitor.admin.problems_index'))
