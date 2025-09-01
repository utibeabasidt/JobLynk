from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash
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

def role_required(required_role):
    """Decorator that requires a specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not utils.user_is_authenticated():
                return redirect(url_for("routes.login"))
            
            if not utils.user_has_role(required_role):
                current_role = utils.get_current_user_role()
                if current_role == 'freelancer':
                    flash("Access denied. You need employer privileges.")
                    return redirect(url_for("routes.freelancers_dashboard"))
                elif current_role == 'employer':
                    flash("Access denied. You need freelancer privileges.")
                    return redirect(url_for("routes.employers_dashboard"))
                else:
                    return redirect(url_for("routes.login"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@routes.route("/")
def index():
    return render_template("index.html")

@routes.route("/logout")
def logout():
    return utils.clear_user_cookies()

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
    if not user or user["password"] != password: 
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
        )
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

# Authenticated routes with role requirements

@routes.route("/employers/dashboard")
@role_required('employer')
def employers_dashboard():
    user_id = utils.get_current_user_id()
    jobs = db.get_jobs_by_employer(user_id)
    user = db.get_user_by_id(user_id)
    return render_template("employers-dashboard.html", jobs=jobs, user=user)

@routes.route("/employer/job/applications/<int:job_id>", methods=["GET"])
@role_required('employer')
def view_job_applications(job_id):
    user_id = utils.get_current_user_id()
    job = next((j for j in db.get_jobs_by_employer(user_id) if j["id"] == job_id), None)
    if not job:
        flash("Job not found or unauthorized!")
        return redirect(url_for("routes.employers_dashboard"))
    applications = [a for a in db.get_applications_for_employer(user_id) if a["job_id"] == job_id]
    return render_template("job-applications.html", job=job, applications=applications)

@routes.route("/employer/upload", methods=["GET", "POST"])
@role_required('employer')
def upload_job():
    user_id = utils.get_current_user_id()
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
@role_required('employer')
def edit_job(job_id):
    user_id = utils.get_current_user_id()
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

@routes.route("/employer/job/delete/<int:job_id>", methods=["POST","GET"])
@role_required('employer')
def delete_job(job_id):
    user_id = utils.get_current_user_id()
    if db.delete_job(job_id, user_id):
        flash("Job deleted successfully!")
    else:
        flash("Failed to delete job or unauthorized!")
    return redirect(url_for("routes.employers_dashboard"))

@routes.route("/freelancers/dashboard")
@role_required('freelancer')
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
@role_required('freelancer')
def apply_job(job_id):
    user_id = utils.get_current_user_id()
    if request.method == "POST":
        about = request.form.get("about")  
        resume = request.files.get("resume")
        if resume and resume.filename:
            upload_folder = os.path.join("static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            
            filename = f"{user_id}_{resume.filename}"
            resume_path = os.path.join(upload_folder, filename)
            resume.save(resume_path)
            
            if db.insert_application(job_id, user_id, about, resume_path):
                flash("Application submitted successfully!")
                return redirect(url_for("routes.freelancers_dashboard"))
            flash("You have already applied for this job!")
        else:
            flash("Please upload a resume!")
    job = next((j for j in db.get_all_jobs() if j["id"] == job_id), None)
    user = db.get_user_by_id(user_id) 
    return render_template("apply-freelancers.html", job_id=job_id, job=job, user=user)


@routes.route("/download_resume/<int:application_id>")
@role_required('employer')
def download_resume(application_id):
    """Download resume for a specific application - deployment ready"""
    user_id = utils.get_current_user_id()
    
    # Get the application and verify the employer owns the job
    application = db.get_application_by_id(application_id)
    if not application:
        flash("Application not found!")
        return redirect(url_for("routes.employers_dashboard"))
    
    # Check if the current employer owns the job this application is for
    job = db.get_job_by_id(application["job_id"])
    if not job or job["employer_id"] != user_id:
        flash("Unauthorized access!")
        return redirect(url_for("routes.employers_dashboard"))
    
    # Check if resume exists - works both locally and in production
    resume_path = application["resume_path"]
    if not resume_path:
        flash("No resume uploaded for this application!")
        return redirect(url_for("routes.view_job_applications", job_id=application["job_id"]))
    
    # Handle both absolute and relative paths for deployment
    if not os.path.isabs(resume_path):
        # If it's a relative path, make it absolute from app root
        resume_path = os.path.join(os.getcwd(), resume_path)
    
    if not os.path.exists(resume_path):
        flash("Resume file not found on server!")
        return redirect(url_for("routes.view_job_applications", job_id=application["job_id"]))
    
    try:
        filename = os.path.basename(resume_path)
        if "_" in filename:
            original_filename = "_".join(filename.split("_")[1:])
        else:
            original_filename = filename
            
        return send_file(
            resume_path,
            as_attachment=True,
            download_name=f"{application['freelancer_name']}_resume_{original_filename}",
            mimetype='application/octet-stream'
        )
    except Exception as e:
        flash("Error downloading resume!")
        return redirect(url_for("routes.view_job_applications", job_id=application["job_id"]))


@routes.route("/contact", methods=['POST'])
def contact():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")
    if not name or not email or not message:
        flash("All fields are required!")
        return redirect(url_for("routes.index") + "#contact")
    
    # Here you would typically handle the contact form submission,
    # e.g., save to database or send an email. For now, we just flash a message.
    if db.insert_contact(name, email, message):
        flash("Thank you for contacting us! We will get back to you soon.")
    else:
        flash("Error submitting your message. Please try again later.")
    return redirect(url_for("routes.index") + "#contact")