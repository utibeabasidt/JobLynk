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
    date_of_birth = request.form.get("date_of_birth")
    if not email or not name or not password or not company_name or not date_of_birth:
        flash("All fields are required!")
        return redirect(url_for("routes.employers_register"))
    user_id = db.insert_user(
        name, email, password, "employer", company_name, date_of_birth
    )
    if not user_id:
        flash("Email already exists!")
        return redirect(url_for("routes.employers_register"))
    return utils.set_user_cookie_and_redirect(user_id, "employer")


# Authenticated routes


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


@routes.route("/employer/job/edit/<int:job_id>", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    user_id = int(request.cookies.get("user_id"))
    job = next((j for j in db.get_jobs_by_employer(user_id) if j["id"] == job_id), None)
    if not job:
        flash("Job not found or unauthorized!")
        return redirect(url_for("routes.employers_dashboard"))
    if request.method == "POST":
        if db.update_job(
            job_id,
            request.form["title"],
            request.form["description"],
            float(request.form["salary"]),
            request.form["job_type"],
            user_id,
        ):
            flash("Job updated successfully!")
            return redirect(url_for("routes.employers_dashboard"))
        flash("Failed to update job!")
    return render_template("edit-job.html", job=job)


@routes.route("/employer/job/delete/<int:job_id>", methods=["POST"])
@login_required
def delete_job(job_id):
    user_id = int(request.cookies.get("user_id"))
    if db.delete_job(job_id, user_id):
        flash("Job deleted successfully!")
    else:
        flash("Failed to delete job or unauthorized!")
    return redirect(url_for("routes.employers_dashboard"))


@routes.route("/freelancers/dashboard")
@login_required
def freelancers_dashboard():
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("search", "").lower()
    per_page = 3  

    all_jobs = db.get_all_jobs()

    jobs_with_employer = []
    for job in all_jobs:
        employer = db.get_user_by_id(job["employer_id"])
        job["company_name"] = (
            employer.get("company_name", "Unknown") if employer else "Unknown"
        )
        jobs_with_employer.append(job)

    if search_query:
        filtered_jobs = [
            job
            for job in jobs_with_employer
            if search_query in job["title"].lower()
            or search_query in job["description"].lower()
        ]
    else:
        filtered_jobs = jobs_with_employer

    total_jobs = len(filtered_jobs)
    total_pages = (total_jobs + per_page - 1) // per_page
    page = max(1, min(page, total_pages))  # Ensure page is within bounds

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    jobs = filtered_jobs[start_idx:end_idx]

    return render_template(
        "freelancers-dashboard.html",
        jobs=jobs,
        total_pages=total_pages,
        current_page=page,
        search_query=search_query,
    )


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
