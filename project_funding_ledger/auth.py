from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from project_funding_ledger.supabase_client import get_supabase_client
from project_funding_ledger.audit import log_audit_event

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
                profile_id = None
                try:
                    profile_res = client.table('user_profile').select('*').eq('auth_user_id', res.user.id).execute()
                    if not profile_res.data:
                        # Fallback create profile row if missing (e.g. trigger didn't run)
                        profile_insert = client.table('user_profile').insert({
                            'auth_user_id': res.user.id,
                            'full_name': res.user.user_metadata.get('full_name', 'New User'),
                            'email': email,
                            'user_type': 'Project Stakeholder',
                            'status': 'Active'
                        }).execute()
                        if profile_insert.data:
                            profile_id = profile_insert.data[0]['id']
                    else:
                        profile_id = profile_res.data[0]['id']
                except Exception:
                    pass
                
                # Log login event
                log_audit_event(
                    client=client,
                    user_id=res.user.id,
                    action_type='Login',
                    entity_type='User',
                    table_name='user_profile',
                    record_id=profile_id,
                    summary=f"User {email} logged in successfully."
                )
                
                # Get user type for redirect routing
                user_type = 'Project Stakeholder'
                try:
                    profile_res = client.table('user_profile').select('user_type').eq('auth_user_id', res.user.id).execute()
                    if profile_res.data:
                        user_type = profile_res.data[0]['user_type']
                except Exception:
                    pass
                
                flash("Welcome back!", "success")
                if user_type == 'System Administrator':
                    return redirect(url_for('org_import.admin_dashboard'))
                else:
                    return redirect(url_for('profile.profile_page'))
        except Exception as e:
            flash(f"Login failed: {str(e)}", "error")
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    client = get_supabase_client()
    try:
        user_res = client.auth.get_user()
        user = user_res.user if user_res else None
        if user:
            profile_id = None
            try:
                profile_res = client.table('user_profile').select('id').eq('auth_user_id', user.id).execute()
                if profile_res.data:
                    profile_id = profile_res.data[0]['id']
            except Exception:
                pass
            
            # Log logout event while session is still active
            log_audit_event(
                client=client,
                user_id=user.id,
                action_type='Logout',
                entity_type='User',
                table_name='user_profile',
                record_id=profile_id,
                summary=f"User {user.email} logged out."
            )
    except Exception:
        pass

    try:
        client.auth.sign_out()
    except Exception:
        pass
    session.pop("access_token", None)
    session.pop("refresh_token", None)
    flash("You have been signed out.", "info")
    return redirect(url_for('auth.login'))

