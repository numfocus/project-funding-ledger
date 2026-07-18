from flask import Blueprint, request, render_template, redirect, url_for, flash
from project_funding_ledger.supabase_client import get_supabase_client

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'])
def profile_page():
    client = get_supabase_client()
    try:
        user = client.auth.get_user()
    except Exception:
        user = None
        
    if not user:
        flash("You must be logged in to view your profile.", "warning")
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        organization = request.form.get('organization')
        
        try:
            # Update user profile in PostgreSQL database via Supabase client
            client.table('user_profile').update({
                'full_name': full_name,
                'organization_affiliation': organization
            }).eq('auth_user_id', user.id).execute()
            
            # Also update user metadata in Supabase Auth
            client.auth.update_user({
                "data": {
                    "full_name": full_name,
                    "organization_affiliation": organization
                }
            })
            
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
            'organization_affiliation': user.user_metadata.get('organization_affiliation', 'N/A'),
            'user_type': 'Project Stakeholder',
            'status': 'Active'
        }
        
    return render_template('profile.html', user_profile=user_profile)
