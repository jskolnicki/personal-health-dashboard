from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__, template_folder='templates')

@home_bp.route('/')
def load_home_page():
    return render_template('home.html')

@home_bp.route('/about')
def about():
    return render_template('about.html')

# @home_bp.route('/projects')
# def projects():
#     return render_template('projects.html')

# @home_bp.route('/contact')
# def contact():
#     return render_template('contact.html')