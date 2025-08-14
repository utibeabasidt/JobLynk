# routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from functools import wraps
import db
import utils
import os

routes = Blueprint('routes', __name__)

# Middleware for authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not utils.user_is_authenticated():
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function

# Public routes
@routes.route('/')
def index():
    if utils.user_is_authenticated():
        user_id = int(request.cookies.get('user_id'))
        user = db.get_user_by_id(user_id)
        return redirect(url_for('routes.freelancer_dashboard' if user['role'] == 'freelancer' else 'routes.employers_dashboard'))
    return render_template('index.html')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password:
        return render_template('login.html', error='Email and Password are required!')
    user = db.get_user_by_email(email)
    if not user or user['password'] != password:  # Replace with hashing
        return render_template('login.html', error='Invalid email or password!')
    return utils.set_user_cookie_and_redirect(user['id'], user['role'])

@routes.route('/employers-register', methods=['GET', 'POST'])
def employer_register():
    if request.method == 'GET':
        return render_template('employers-register.html')
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    role = request.form.get('role')
    company_name = request.form.get('company_name') if role == 'employer' else None
    if not email or not name or not password or not role:
        return render_template('employers-register.html', error='All fields are required!')
    user_id = db.insert_user(name, email, password, role, company_name)
    if not user_id:
        return render_template('employers-register.html', error='Email already exists!')
    return utils.set_user_cookie_and_redirect(user_id, role)


@routes.route('/freelancers-register', methods=['GET', 'POST'])
def freelance_register():
    if request.method == 'GET':
        return render_template('freelancers-register.html')
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    role = request.form.get('role')
    company_name = request.form.get('company_name') if role == 'employer' else None
    if not email or not name or not password or not role:
        return render_template('freelancers-register.html', error='All fields are required!')
    user_id = db.insert_user(name, email, password, role, company_name)
    if not user_id:
        return render_template('freelancers-register.html', error='Email already exists!')
    return utils.set_user_cookie_and_redirect(user_id, role)


# Dashboard routes
@routes.route('/freelancer/dashboard')
@login_required
def freelancer_dashboard():
    jobs = db.get_all_jobs()
    return render_template('freelancer-dashboard.html', jobs=jobs)

@routes.route('/employers/dashboard')
@login_required
def employers_dashboard():
    user_id = int(request.cookies.get('user_id'))
    jobs = db.get_jobs_by_employer(user_id)
    return render_template('employers-dashboard.html', jobs=jobs)

@routes.route('/employer/upload', methods=['GET', 'POST'])
@login_required
def upload_job():
    user_id = int(request.cookies.get('user_id'))
    if request.method == 'POST':
        job_id = db.insert_job(request.form['title'], request.form['description'],
                               float(request.form['salary']), request.form['job_type'], user_id)
        if job_id:
            flash('Job uploaded successfully!')
            return redirect(url_for('routes.employers_dashboard'))
        flash('Failed to upload job!')
    return render_template('upload-employers.html')

# Apply route
@routes.route('/job/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    user_id = int(request.cookies.get('user_id'))
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter')
        resume = request.files.get('resume')
        if resume and resume.filename:
            upload_folder = os.path.join('static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            resume_path = os.path.join(upload_folder, f"{user_id}_{resume.filename}")
            resume.save(resume_path)
            if db.insert_application(job_id, user_id, cover_letter, resume_path):
                flash('Application submitted successfully!')
                return redirect(url_for('routes.freelancer_dashboard'))
            flash('You have already applied for this job!')
        else:
            flash('Please upload a resume!')
    job = next((j for j in db.get_all_jobs() if j['id'] == job_id), None)  
    return render_template('apply-freelancers.html', job_id=job_id, job=job)