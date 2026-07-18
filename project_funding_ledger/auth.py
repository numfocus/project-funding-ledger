from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from project_funding_ledger.supabase_client import get_supabase_client

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        organization = request.form.get('organization')
        
        client = get_supabase_client()
        try:
            # Sign up in Supabase Auth
            res = client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "organization_affiliation": organization
                    }
                }
            })
            
            # If auto-confirm is enabled in the local Supabase config,
            # we get the session immediately.
            if res.session:
                session["access_token"] = res.session.access_token
                session["refresh_token"] = res.session.refresh_token
                
                # Check if user profile row was created by trigger.
                # If not, let's create a backup profile row.
                try:
                    profile_res = client.table('user_profile').select('*').eq('auth_user_id', res.user.id).execute()
                    if not profile_res.data:
                        client.table('user_profile').insert({
                            'auth_user_id': res.user.id,
                            'full_name': full_name,
                            'email': email,
                            'organization_affiliation': organization,
                            'user_type': 'Project Stakeholder',
                            'status': 'Active'
                        }).execute()
                except Exception:
                    pass
                    
                flash("Signup and login successful!", "success")
                return redirect(url_for('profile.profile_page'))
            else:
                flash("Signup successful! Please check your email inbox to confirm.", "info")
                return redirect(url_for('auth.login'))
                
        except Exception as e:
            flash(f"Signup failed: {str(e)}", "error")
            
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        client = get_supabase_client()
        try:
            res = client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if res.session:
                session["access_token"] = res.session.access_token
                session["refresh_token"] = res.session.refresh_token
                
                # Verify user_profile row exists
                try:
                    profile_res = client.table('user_profile').select('*').eq('auth_user_id', res.user.id).execute()
                    if not profile_res.data:
                        # Fallback create profile row if missing (e.g. trigger didn't run)
                        client.table('user_profile').insert({
                            'auth_user_id': res.user.id,
                            'full_name': res.user.user_metadata.get('full_name', 'New User'),
                            'email': email,
                            'organization_affiliation': res.user.user_metadata.get('organization_affiliation'),
                            'user_type': 'Project Stakeholder',
                            'status': 'Active'
                        }).execute()
                except Exception:
                    pass
                
                flash("Welcome back!", "success")
                return redirect(url_for('profile.profile_page'))
        except Exception as e:
            flash(f"Login failed: {str(e)}", "error")
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    client = get_supabase_client()
    try:
        client.auth.sign_out()
    except Exception:
        pass
    session.pop("access_token", None)
    session.pop("refresh_token", None)
    flash("You have been signed out.", "info")
    return redirect(url_for('auth.login'))
