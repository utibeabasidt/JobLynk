# routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
import db
import utils
import os
from functools import wraps

routes = Blueprint("routes", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not utils.user_is_authenticated():
            return redirect(url_for("routes.login"))
        return f(*args, **kwargs)

    return decorated_function


@routes.route("/")
def index():
    return render_template("index.html")


@routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    email = request.form.get("email")
    password = request.form.get("password")
    if not email or not password:
        flash("Email and Password are required!")
        return redirect(url_for("routes.login"))
    user = db.get_user_by_email(email)
    if not user or user["password"] != password:  # Replace with hashing
        flash("Invalid email or password!")
        return redirect(url_for("routes.login"))
    return utils.set_user_cookie_and_redirect(user["id"], user["role"])


@routes.route("/change-password", methods=["GET", "POST"])
def change_password():
    if request.method == "GET":
        return render_template("change-password.html")
    email = request.form.get("email")
    new_password = request.form.get("password")
    if not email or not new_password:
        flash("Email and new password are required!")
        return redirect(url_for("routes.change_password"))
    user = db.get_user_by_email(email)
    if user:
        db.insert_user(
            user["name"], email, new_password, user["role"], user["company_name"]
        )  # Simplified reset
        flash("Password changed successfully!")
        return redirect(url_for("routes.login"))
    flash("Email not found!")
    return redirect(url_for("routes.change_password"))


@routes.route("/freelancers/register", methods=["GET", "POST"])
def freelancers_register():
    if request.method == "GET":
        return render_template("freelancers-register.html")
    email = request.form.get("email")
    name = request.form.get("name")
    password = request.form.get("password")
    if not email or not name or not password:
        flash("All fields are required!")
        return redirect(url_for("routes.freelancers_register"))
    user_id = db.insert_user(name, email, password, "freelancer")
    if not user_id:
        flash("Email already exists!")
        return redirect(url_for("routes.freelancers_register"))
    return utils.set_user_cookie_and_redirect(user_id, "freelancer")


@routes.route("/employers/register", methods=["GET", "POST"])
def employers_register():
    if request.method == "GET":
        return render_template("employers-register.html")
    email = request.form.get("email")
    name = request.form.get("name")
    password = request.form.get("password")
    company_name = request.form.get("company_name")
    if not email or not name or not password or not company_name:
        flash("All fields are required!")
        return redirect(url_for("routes.employers_register"))
    user_id = db.insert_user(name, email, password, "employer", company_name)
    if not user_id:
        flash("Email already exists!")
        return redirect(url_for("routes.employers_register"))
    return utils.set_user_cookie_and_redirect(user_id, "employer")


# Authenticated routes
@routes.route("/freelancers/dashboard")
@login_required
def freelancers_dashboard():
    jobs = db.get_all_jobs()
    return render_template("freelancers-dashboard.html", jobs=jobs)


@routes.route("/employers/dashboard")
@login_required
def employers_dashboard():
    user_id = int(request.cookies.get("user_id"))
    jobs = db.get_jobs_by_employer(user_id)
    user = db.get_user_by_id(user_id)
    return render_template("employers-dashboard.html", jobs=jobs, user=user)


@routes.route("/employer/upload", methods=["GET", "POST"])
@login_required
def upload_job():
    user_id = int(request.cookies.get("user_id"))
    if request.method == "POST":
        job_id = db.insert_job(
            request.form["title"],
            request.form["description"],
            float(request.form["salary"]),
            request.form["job_type"],
            user_id,
        )
        if job_id:
            flash("Job uploaded successfully!")
            return redirect(url_for("routes.employers_dashboard"))
        flash("Failed to upload job!")
    return render_template("upload-employers.html")


@routes.route("/job/apply/<int:job_id>", methods=["GET", "POST"])
@login_required
def apply_job(job_id):
    user_id = int(request.cookies.get("user_id"))
    if request.method == "POST":
        cover_letter = request.form.get("cover_letter")
        resume = request.files.get("resume")
        if resume and resume.filename:
            upload_folder = os.path.join("static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            resume_path = os.path.join(upload_folder, f"{user_id}_{resume.filename}")
            resume.save(resume_path)
            if db.insert_application(job_id, user_id, cover_letter, resume_path):
                flash("Application submitted successfully!")
                return redirect(url_for("routes.freelancers_dashboard"))
            flash("You have already applied for this job!")
        else:
            flash("Please upload a resume!")
    job = next((j for j in db.get_all_jobs() if j["id"] == job_id), None)
    return render_template("apply-freelancers.html", job_id=job_id, job=job)
