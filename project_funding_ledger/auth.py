from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from project_funding_ledger.supabase_client import get_supabase_client

auth_bp = Blueprint('auth', __name__)

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
