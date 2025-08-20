# utils.py
from flask import make_response, request, redirect, url_for

def user_is_authenticated():
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')
    return user_id and role in ['freelancer', 'employer']

def set_user_cookie_and_redirect(user_id, role):
    response = make_response(redirect(url_for('routes.freelancers_dashboard' if role == 'freelancer' else 'routes.employers_dashboard')))
    response.set_cookie('user_id', str(user_id), max_age=9900) 
    response.set_cookie('role', role, max_age=3600)
    return response