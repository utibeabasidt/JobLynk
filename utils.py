# utils.py
from flask import make_response, request, redirect, url_for
import db

def user_is_authenticated():
    """Check if user has valid authentication cookies"""
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')
    return user_id and role in ['freelancer', 'employer']

def user_has_role(required_role):
    """Check if authenticated user has the required role"""
    if not user_is_authenticated():
        return False
    
    user_id = request.cookies.get('user_id')
    cookie_role = request.cookies.get('role')
    
    # Verify the role matches what's in the database (security check)
    user = db.get_user_by_id(int(user_id))
    if not user or user['role'] != cookie_role:
        return False
    
    return cookie_role == required_role

def get_current_user_role():
    """Get the current user's role from cookies"""
    return request.cookies.get('role')

def get_current_user_id():
    """Get the current user's ID from cookies"""
    user_id = request.cookies.get('user_id')
    return int(user_id) if user_id else None

def set_user_cookie_and_redirect(user_id, role):
    """Set user cookies and redirect to appropriate dashboard"""
    if role == 'freelancer':
        response = make_response(redirect(url_for('routes.freelancers_dashboard')))
    else:
        response = make_response(redirect(url_for('routes.employers_dashboard')))
    
    response.set_cookie('user_id', str(user_id), max_age=3600)  # 1 hour
    response.set_cookie('role', role, max_age=3600)  # 1 hour
    return response

def clear_user_cookies():
    """Clear user authentication cookies"""
    response = make_response(redirect(url_for('routes.index')))
    response.set_cookie('user_id', '', expires=0)
    response.set_cookie('role', '', expires=0)
    return response