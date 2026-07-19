from flask import Blueprint, request, render_template, redirect, url_for, flash
from project_funding_ledger.supabase_client import get_supabase_client
from project_funding_ledger.audit import log_audit_event

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'])
def profile_page():
    client = get_supabase_client()
    try:
        user_response = client.auth.get_user()
        user = user_response.user if user_response else None
    except Exception:
        user = None
        
    if not user:
        flash("You must be logged in to view your profile.", "warning")
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        
        try:
            # Fetch existing profile first to log changes (old vs new value)
            old_profile_res = client.table('user_profile').select('*').eq('auth_user_id', user.id).execute()
            old_profile = old_profile_res.data[0] if old_profile_res.data else None
            old_full_name = old_profile.get('full_name') if old_profile else None
            profile_id = old_profile.get('id') if old_profile else None

            # Update user profile in PostgreSQL database via Supabase client
            client.table('user_profile').update({
                'full_name': full_name
            }).eq('auth_user_id', user.id).execute()
            
            # Also update user metadata in Supabase Auth
            client.auth.update_user({
                "data": {
                    "full_name": full_name
                }
            })
            
            # Log profile update event
            log_audit_event(
                client=client,
                user_id=user.id,
                action_type='Update',
                entity_type='User',
                table_name='user_profile',
                record_id=profile_id,
                old_value={'full_name': old_full_name} if old_full_name is not None else None,
                new_value={'full_name': full_name},
                summary=f"User updated profile name from '{old_full_name}' to '{full_name}'."
            )
            
            flash("Profile updated successfully!", "success")
        except Exception as e:
            flash(f"Error updating profile: {str(e)}", "error")
            
    # Fetch current profile details from the user_profile table
    try:
        res = client.table('user_profile').select('*').eq('auth_user_id', user.id).execute()
        user_profile = res.data[0] if res.data else None
    except Exception as e:
        flash(f"Error fetching profile: {str(e)}", "error")
        user_profile = None
        
    if not user_profile:
        # Fallback profile from token metadata if database fetch fails or row does not exist yet
        user_profile = {
            'email': user.email,
            'full_name': user.user_metadata.get('full_name', 'N/A'),
            'user_type': 'Project Stakeholder',
            'status': 'Active'
        }
        
    return render_template('profile.html', user_profile=user_profile)

