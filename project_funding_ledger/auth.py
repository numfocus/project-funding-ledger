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
                            'user_type': 'Organization Stakeholder',
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
                user_type = 'Organization Stakeholder'
                try:
                    profile_res = client.table('user_profile').select('user_type').eq('auth_user_id', res.user.id).execute()
                    if profile_res.data:
                        user_type = profile_res.data[0]['user_type']
                except Exception:
                    pass
                
                if user_type == 'System Administrator':
                    return redirect(url_for('org_import.admin_dashboard'))
                else:
                    try:
                        profile_res = client.table('user_profile').select('id').eq('auth_user_id', res.user.id).single().execute()
                        if profile_res.data:
                            user_profile_id = profile_res.data['id']
                            perms_res = client.table('organization_permission').select('organization_id').eq('user_id', user_profile_id).eq('status', 'Active').execute()
                            perms = perms_res.data or []
                            if len(perms) == 1:
                                return redirect(url_for('org.org_detail', org_id=perms[0]['organization_id']))
                    except Exception:
                        pass
                    return redirect(url_for('org.dashboard'))
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


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    client = get_supabase_client()
    verified_email = request.args.get('email', '').strip()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'check_invite':
            email = request.form.get('email', '').strip().lower()
            if not email:
                flash("Please enter an email address.", "error")
                return render_template('register.html')
                
            try:
                # Call RPC function in supabase to check if email is invited
                res = client.rpc('is_email_invited', {'check_email': email}).execute()
                is_invited = res.data if res else False
                
                if is_invited:
                    flash("Invitation verified! Please complete your registration details.", "success")
                    return redirect(url_for('auth.register', email=email))
                else:
                    flash("This email address is not invited or has already been registered.", "error")
                    return render_template('register.html')
            except Exception as e:
                flash(f"Verification failed: {str(e)}", "error")
                return render_template('register.html')
                
        elif action == 'complete_registration':
            email = request.form.get('email', '').strip().lower()
            full_name = request.form.get('full_name', '').strip()
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not email or not full_name or not password:
                flash("All fields are required.", "error")
                return render_template('register.html', verified_email=email)
                
            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return render_template('register.html', verified_email=email)
                
            # Double check invite in backend to be secure
            try:
                res = client.rpc('is_email_invited', {'check_email': email}).execute()
                if not res or not res.data:
                    flash("Verification failed: This email is no longer invited or is already registered.", "error")
                    return redirect(url_for('auth.register'))
            except Exception as e:
                flash(f"Verification check failed: {str(e)}", "error")
                return render_template('register.html', verified_email=email)
                
            # Perform signup with Supabase Auth
            try:
                signup_res = client.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "full_name": full_name
                        }
                    }
                })
                
                # Check if signed up successfully
                if signup_res and signup_res.user:
                    # Supabase returns session if email confirmation is disabled
                    if signup_res.session:
                        session["access_token"] = signup_res.session.access_token
                        session["refresh_token"] = signup_res.session.refresh_token
                        
                        # Fallback query profile_id for logging
                        profile_id = None
                        try:
                            profile_res = client.table('user_profile').select('id, user_type').eq('auth_user_id', signup_res.user.id).execute()
                            if profile_res.data:
                                profile_id = profile_res.data[0]['id']
                                user_type = profile_res.data[0]['user_type']
                            else:
                                user_type = 'Organization Stakeholder'
                        except Exception:
                            user_type = 'Organization Stakeholder'
                            
                        # Log registration and login
                        log_audit_event(
                            client=client,
                            user_id=signup_res.user.id,
                            action_type='Login',
                            entity_type='User',
                            table_name='user_profile',
                            record_id=profile_id,
                            summary=f"User {email} registered and logged in successfully."
                        )
                        
                        flash("Registration successful! Welcome.", "success")
                        if user_type == 'System Administrator':
                            return redirect(url_for('org_import.admin_dashboard'))
                        else:
                            try:
                                profile_res = client.table('user_profile').select('id').eq('auth_user_id', signup_res.user.id).single().execute()
                                if profile_res.data:
                                    user_profile_id = profile_res.data['id']
                                    perms_res = client.table('organization_permission').select('organization_id').eq('user_id', user_profile_id).eq('status', 'Active').execute()
                                    perms = perms_res.data or []
                                    if len(perms) == 1:
                                        return redirect(url_for('org.org_detail', org_id=perms[0]['organization_id']))
                            except Exception:
                                pass
                            return redirect(url_for('org.dashboard'))
                    else:
                        flash("Registration successful! Please check your email for a confirmation link.", "success")
                        return redirect(url_for('auth.login'))
                else:
                    flash("Registration failed. Please try again.", "error")
                    return render_template('register.html', verified_email=email)
                    
            except Exception as e:
                flash(f"Registration failed: {str(e)}", "error")
                return render_template('register.html', verified_email=email)
                
    # GET request
    if verified_email:
        # Verify the email parameter is actually invited/valid in DB
        try:
            res = client.rpc('is_email_invited', {'check_email': verified_email}).execute()
            if res and res.data:
                return render_template('register.html', verified_email=verified_email)
            else:
                flash("Invalid or expired invitation link.", "error")
                return redirect(url_for('auth.register'))
        except Exception:
            return redirect(url_for('auth.register'))
            
    return render_template('register.html')


