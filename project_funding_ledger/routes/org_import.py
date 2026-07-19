import os
import uuid
import datetime
from flask import Blueprint, request, jsonify, abort, current_app, render_template, redirect, url_for, flash
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from project_funding_ledger.supabase_client import get_supabase_client
from project_funding_ledger.queue import get_queue_client

org_import_bp = Blueprint('org_import', __name__)

def check_admin(client):
    """
    Checks if the user in the current Supabase client context has System Admin role.
    """
    try:
        user_res = client.auth.get_user()
        if not user_res or not user_res.user:
            abort(401, "Authentication required")
        user = user_res.user
        profile = client.table('user_profile').select('id, user_type').eq('auth_user_id', user.id).single().execute()
        if not profile.data or profile.data.get('user_type') != 'System Administrator':
            abort(403, "Admin privileges required")
        return {
            "user": user,
            "profile_id": profile.data.get('id')
        }
    except Exception as e:
        if isinstance(e, HTTPException) or hasattr(e, 'code'):
            raise e
        abort(401, f"Authentication failed: {str(e)}")


@org_import_bp.route('/admin/import/organizations', methods=['POST'])
def import_organizations():
    """
    Saves an uploaded Excel spreadsheet, creates a staging batch,
    and enqueues the parsing task in the background.
    """
    client = get_supabase_client()
    user_info = check_admin(client)
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        return jsonify({"error": "Only Excel (.xlsx, .xls) files are supported"}), 400
        
    # Save the file to a temporary location
    imports_dir = os.path.join(current_app.instance_path, 'imports')
    os.makedirs(imports_dir, exist_ok=True)
    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    file_path = os.path.join(imports_dir, filename)
    file.save(file_path)
    
    try:
        # Create a new import batch record in the database
        batch_res = client.table('organization_import_batch').insert({
            "file_name": file.filename,
            "created_by_user_id": user_info["profile_id"]
        }).execute()
        
        if not batch_res.data:
            raise ValueError("Failed to create import batch record.")
            
        batch_id = batch_res.data[0]['id']
        
        # Cancel all pending/error rows in previous batches
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        client.table('organization_import_row').update({
            "status": "Cancelled",
            "resolved_by_user_id": user_info["profile_id"],
            "resolved_at": now
        }).neq('batch_id', batch_id).in_('status', ['Pending', 'Error']).execute()
        
        # Enqueue the background task
        from flask import session
        access_token = session.get("access_token")
        refresh_token = session.get("refresh_token")
        
        queue = get_queue_client()
        queue.enqueue(
            "process_organization_import",
            file_path=file_path,
            batch_id=batch_id,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        return jsonify({
            "message": "Excel import started successfully in the background.",
            "batch_id": batch_id
        }), 202
        
    except Exception as e:
        # Clean up temporary file on failure
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Failed to start import: {str(e)}"}), 500

@org_import_bp.route('/admin/import/organizations/batches/<batch_id>', methods=['GET'])
def get_import_batch(batch_id):
    """
    Fetches the details and staging rows of a specific import batch.
    """
    client = get_supabase_client()
    check_admin(client)
    
    try:
        # Fetch batch details
        batch_res = client.table('organization_import_batch').select('*').eq('id', batch_id).single().execute()
        if not batch_res.data:
            return jsonify({"error": "Import batch not found"}), 404
            
        # Fetch all rows for this batch
        rows_res = client.table('organization_import_row').select('*').eq('batch_id', batch_id).execute()
        
        return jsonify({
            "batch": batch_res.data,
            "rows": rows_res.data or []
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch batch preview: {str(e)}"}), 500

@org_import_bp.route('/admin/import/organizations/rows/<row_id>/confirm', methods=['POST'])
def confirm_import_row(row_id):
    """
    Enqueues the confirmation task to apply a single staging row to the main DB.
    """
    client = get_supabase_client()
    check_admin(client)
    
    try:
        # Verify row exists and is Pending
        row_res = client.table('organization_import_row').select('*').eq('id', row_id).single().execute()
        if not row_res.data:
            return jsonify({"error": "Import row not found"}), 404
            
        row = row_res.data
        if row['status'] != 'Pending':
            return jsonify({"error": f"Import row cannot be confirmed because status is '{row['status']}'"}), 400
            
        # Enqueue task to apply this single edit
        from flask import session
        access_token = session.get("access_token")
        refresh_token = session.get("refresh_token")
        
        queue = get_queue_client()
        queue.enqueue(
            "confirm_organization_import_row",
            row_id=row_id,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        return jsonify({"message": "Confirmation task enqueued in the background."}), 202
        
    except Exception as e:
        return jsonify({"error": f"Failed to confirm row: {str(e)}"}), 500

@org_import_bp.route('/admin/import/organizations/rows/<row_id>/cancel', methods=['POST'])
def cancel_import_row(row_id):
    """
    Directly marks a staging row as Cancelled.
    """
    client = get_supabase_client()
    user_info = check_admin(client)
    
    try:
        # Verify row exists and is Pending
        row_res = client.table('organization_import_row').select('*').eq('id', row_id).single().execute()
        if not row_res.data:
            return jsonify({"error": "Import row not found"}), 404
            
        row = row_res.data
        if row['status'] != 'Pending':
            return jsonify({"error": f"Import row cannot be cancelled because status is '{row['status']}'"}), 400
            
        # Cancel row directly in the database
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        client.table('organization_import_row').update({
            "status": "Cancelled",
            "resolved_by_user_id": user_info["profile_id"],
            "resolved_at": now
        }).eq('id', row_id).execute()
        
        return jsonify({"message": "Import row cancelled successfully."}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to cancel row: {str(e)}"}), 500


@org_import_bp.route('/admin/import/organizations/batches/<batch_id>/confirm-all', methods=['POST'])
def confirm_all_import_batch(batch_id):
    """
    Enqueues confirmation tasks for all Pending rows in the specified batch.
    """
    client = get_supabase_client()
    check_admin(client)
    
    try:
        rows_res = client.table('organization_import_row').select('id').eq('batch_id', batch_id).eq('status', 'Pending').execute()
        rows = rows_res.data or []
        
        if not rows:
            return jsonify({"message": "No pending rows in this batch to confirm."}), 200
            
        from flask import session
        access_token = session.get("access_token")
        refresh_token = session.get("refresh_token")
        queue = get_queue_client()
        
        for row in rows:
            queue.enqueue(
                "confirm_organization_import_row",
                row_id=row['id'],
                access_token=access_token,
                refresh_token=refresh_token
            )
            
        return jsonify({"message": f"Confirmation tasks for {len(rows)} rows enqueued in the background."}), 202
    except Exception as e:
        return jsonify({"error": f"Failed to confirm all rows: {str(e)}"}), 500


@org_import_bp.route('/admin/import/organizations/batches/<batch_id>/cancel-all', methods=['POST'])
def cancel_all_import_batch(batch_id):
    """
    Directly marks all Pending and Error rows in the specified batch as Cancelled.
    """
    client = get_supabase_client()
    user_info = check_admin(client)
    profile_id = user_info["profile_id"]
    
    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        client.table('organization_import_row').update({
            "status": "Cancelled",
            "resolved_by_user_id": profile_id,
            "resolved_at": now
        }).eq('batch_id', batch_id).in_('status', ['Pending', 'Error']).execute()
        
        return jsonify({"message": "All pending and error rows in this batch cancelled successfully."}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to cancel all rows: {str(e)}"}), 500


@org_import_bp.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """
    Renders the admin dashboard SPA page.
    """
    client = get_supabase_client()
    try:
        check_admin(client)
    except Exception:
        flash("Admin privileges required.", "error")
        return redirect(url_for('auth.login'))
        
    return render_template('admin_dashboard.html')


@org_import_bp.route('/api/admin/organizations', methods=['GET'])
def api_organizations():
    """
    JSON API returning all organizations and their overhead internals.
    """
    client = get_supabase_client()
    try:
        check_admin(client)
    except Exception as e:
        return jsonify({"error": str(e)}), 403
        
    try:
        orgs_res = client.table('organization').select('*').order('organization_name').execute()
        orgs_internal_res = client.table('organization_internal').select('*').execute()
        internal_map = {row['id']: row for row in (orgs_internal_res.data or [])}
        
        orgs = []
        for org in (orgs_res.data or []):
            internal = internal_map.get(org['id'], {})
            orgs.append({
                "id": org['id'],
                "organization_name": org.get("organization_name"),
                "organization_slug": org.get("organization_slug"),
                "status": org.get("status"),
                "organization_type": org.get("organization_type"),
                "description": org.get("description"),
                "website_url": org.get("website_url"),
                "source_code_url": org.get("source_code_url"),
                "donation_url": org.get("donation_url"),
                "join_date": org.get("join_date"),
                "overhead_grant": internal.get("overhead_grant", 0.0),
                "overhead_donation_general": internal.get("overhead_donation_general", 0.0),
                "overhead_donation_corporate": internal.get("overhead_donation_corporate", 0.0),
                "notes": internal.get("notes", "")
            })
        return jsonify(orgs), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@org_import_bp.route('/api/admin/imports/batches', methods=['GET'])
def api_import_batches():
    """
    JSON API returning all import batches and their status counts.
    """
    client = get_supabase_client()
    try:
        check_admin(client)
    except Exception as e:
        return jsonify({"error": str(e)}), 403
        
    try:
        batches_res = client.table('organization_import_batch').select('*').order('created_at', desc=True).execute()
        batches = []
        for batch in (batches_res.data or []):
            rows_res = client.table('organization_import_row').select('status').eq('batch_id', batch['id']).execute()
            rows = rows_res.data or []
            
            pending_count = sum(1 for r in rows if r['status'] == 'Pending')
            confirmed_count = sum(1 for r in rows if r['status'] == 'Confirmed')
            cancelled_count = sum(1 for r in rows if r['status'] == 'Cancelled')
            error_count = sum(1 for r in rows if r['status'] == 'Error')
            
            batches.append({
                "id": batch['id'],
                "file_name": batch.get("file_name"),
                "created_by_user_id": batch.get("created_by_user_id"),
                "created_at": batch.get("created_at"),
                "pending_count": pending_count,
                "confirmed_count": confirmed_count,
                "cancelled_count": cancelled_count,
                "error_count": error_count,
                "total_count": len(rows)
            })
        return jsonify(batches), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@org_import_bp.route('/api/admin/users', methods=['GET'])
def api_users():
    """
    JSON API returning all non-deleted user profiles.
    """
    client = get_supabase_client()
    try:
        check_admin(client)
    except Exception as e:
        return jsonify({"error": str(e)}), 403
        
    try:
        res = client.table('user_profile').select('*').is_('deleted_at', 'null').order('created_at', desc=True).execute()
        return jsonify(res.data or []), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@org_import_bp.route('/api/admin/users', methods=['POST'])
def api_create_user():
    """
    Creates a new User Profile before registration.
    """
    client = get_supabase_client()
    try:
        user_info = check_admin(client)
        admin_profile_id = user_info["profile_id"]
    except Exception as e:
        return jsonify({"error": str(e)}), 403
        
    data = request.json or {}
    email = data.get('email')
    full_name = data.get('full_name')
    user_type = data.get('user_type', 'Organization Stakeholder')
    status = data.get('status', 'Invited')
    
    if not email or not full_name:
        return jsonify({"error": "Email and Full Name are required"}), 400
        
    # Check valid user_type and status
    valid_types = ['System Administrator', 'Program Manager', 'Organization Stakeholder']
    valid_statuses = ['Active', 'Invited', 'Inactive', 'Suspended']
    
    if user_type not in valid_types:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join(valid_types)}"}), 400
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
        
    try:
        # Check if active profile with email already exists
        existing = client.table('user_profile').select('*').eq('email', email).is_('deleted_at', 'null').execute()
        if existing.data:
            return jsonify({"error": "A user profile with this email already exists."}), 400
            
        res = client.table('user_profile').insert({
            'email': email,
            'full_name': full_name,
            'user_type': user_type,
            'status': status,
            'created_by_user_id': admin_profile_id,
            'updated_by_user_id': admin_profile_id
        }).execute()
        
        if not res.data:
            raise ValueError("Failed to create user profile in DB")
            
        new_profile = res.data[0]
        
        # Log event
        from project_funding_ledger.audit import log_audit_event_async
        log_audit_event_async(
            user_id=user_info["user"].id,
            action_type='Create',
            entity_type='User',
            table_name='user_profile',
            record_id=new_profile['id'],
            new_value=new_profile,
            summary=f"Admin created User Profile for {email} with role {user_type} and status {status}."
        )
        
        return jsonify(new_profile), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@org_import_bp.route('/api/admin/users/<user_id>', methods=['PUT'])
def api_update_user(user_id):
    """
    Updates an existing user profile (role, status, full name).
    """
    client = get_supabase_client()
    try:
        user_info = check_admin(client)
        admin_profile_id = user_info["profile_id"]
    except Exception as e:
        return jsonify({"error": str(e)}), 403
        
    data = request.json or {}
    
    update_data = {}
    if 'full_name' in data:
        update_data['full_name'] = data['full_name']
    if 'user_type' in data:
        update_data['user_type'] = data['user_type']
    if 'status' in data:
        update_data['status'] = data['status']
        
    if not update_data:
        return jsonify({"error": "No update fields provided."}), 400
        
    # Check valid user_type and status if they are being updated
    valid_types = ['System Administrator', 'Program Manager', 'Organization Stakeholder']
    valid_statuses = ['Active', 'Invited', 'Inactive', 'Suspended']
    
    if 'user_type' in update_data and update_data['user_type'] not in valid_types:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join(valid_types)}"}), 400
    if 'status' in update_data and update_data['status'] not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
        
    update_data['updated_by_user_id'] = admin_profile_id
    
    try:
        # Get old value for audit logging
        old_profile_res = client.table('user_profile').select('*').eq('id', user_id).execute()
        if not old_profile_res.data:
            return jsonify({"error": "User profile not found."}), 404
        old_profile = old_profile_res.data[0]
        
        res = client.table('user_profile').update(update_data).eq('id', user_id).execute()
        if not res.data:
            raise ValueError("Failed to update user profile.")
            
        updated_profile = res.data[0]
        
        # Log event
        from project_funding_ledger.audit import log_audit_event_async
        log_audit_event_async(
            user_id=user_info["user"].id,
            action_type='Update',
            entity_type='User',
            table_name='user_profile',
            record_id=user_id,
            old_value=old_profile,
            new_value=updated_profile,
            summary=f"Admin updated User Profile for {old_profile['email']}."
        )
        
        return jsonify(updated_profile), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@org_import_bp.route('/api/admin/users/<user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    """
    Soft-deletes a user profile.
    """
    client = get_supabase_client()
    try:
        user_info = check_admin(client)
        admin_profile_id = user_info["profile_id"]
    except Exception as e:
        return jsonify({"error": str(e)}), 403
        
    try:
        old_profile_res = client.table('user_profile').select('*').eq('id', user_id).execute()
        if not old_profile_res.data:
            return jsonify({"error": "User profile not found."}), 404
        old_profile = old_profile_res.data[0]
        
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        res = client.table('user_profile').update({
            'deleted_at': now,
            'deleted_by_user_id': admin_profile_id
        }).eq('id', user_id).execute()
        
        # Log event
        from project_funding_ledger.audit import log_audit_event_async
        log_audit_event_async(
            user_id=user_info["user"].id,
            action_type='Delete',
            entity_type='User',
            table_name='user_profile',
            record_id=user_id,
            old_value=old_profile,
            summary=f"Admin soft-deleted User Profile for {old_profile['email']}."
        )
        
        return jsonify({"message": "User profile deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@org_import_bp.route('/api/admin/users/<user_id>/permissions', methods=['GET'])
def api_user_permissions(user_id):
    """
    JSON API returning active organization permissions for a user.
    """
    client = get_supabase_client()
    try:
        check_admin(client)
    except Exception as e:
        return jsonify({"error": str(e)}), 403
        
    try:
        # Fetch active permissions for this user, joining with organization
        res = client.table('organization_permission') \
            .select('*, organization:organization_id(organization_name)') \
            .eq('user_id', user_id) \
            .eq('status', 'Active') \
            .execute()
        return jsonify(res.data or []), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@org_import_bp.route('/api/admin/users/<user_id>/permissions', methods=['POST'])
def api_grant_user_permission(user_id):
    """
    JSON API to grant organization access to a user.
    """
    client = get_supabase_client()
    try:
        user_info = check_admin(client)
        admin_profile_id = user_info["profile_id"]
    except Exception as e:
        return jsonify({"error": str(e)}), 403
        
    data = request.json or {}
    organization_id = data.get('organization_id')
    permission_level = data.get('permission_level', 'View')
    notes = data.get('notes', '')
    
    if not organization_id:
        return jsonify({"error": "Organization ID is required"}), 400
        
    if permission_level not in ['View', 'Edit Metadata', 'Manage']:
        return jsonify({"error": "Invalid permission level"}), 400
        
    try:
        # Check if user profile exists
        target_user = client.table('user_profile').select('id, email, full_name').eq('id', user_id).is_('deleted_at', 'null').execute()
        if not target_user.data:
            return jsonify({"error": "Target user not found"}), 404
        user_email = target_user.data[0].get('email')
        
        # Check if organization exists
        org = client.table('organization').select('id, organization_name').eq('id', organization_id).execute()
        if not org.data:
            return jsonify({"error": "Organization not found"}), 404
        org_name = org.data[0].get('organization_name')
        
        # Check if active permission already exists
        existing = client.table('organization_permission') \
            .select('id') \
            .eq('user_id', user_id) \
            .eq('organization_id', organization_id) \
            .eq('status', 'Active') \
            .execute()
        if existing.data:
            return jsonify({"error": "User already has active permission for this organization"}), 400
            
        # Insert permission record
        res = client.table('organization_permission').insert({
            'user_id': user_id,
            'organization_id': organization_id,
            'permission_level': permission_level,
            'status': 'Active',
            'created_by_user_id': admin_profile_id,
            'notes': notes
        }).execute()
        
        if not res.data:
            raise ValueError("Failed to insert permission record")
            
        new_permission = res.data[0]
        
        # Log audit event
        from project_funding_ledger.audit import log_audit_event_async
        log_audit_event_async(
            user_id=user_info["user"].id,
            action_type='Permission Change',
            entity_type='User',
            table_name='organization_permission',
            record_id=new_permission['id'],
            related_organization_id=organization_id,
            new_value=new_permission,
            summary=f"Admin granted '{permission_level}' permission to user {user_email} for organization '{org_name}'."
        )
        
        return jsonify(new_permission), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@org_import_bp.route('/api/admin/users/permissions/<permission_id>', methods=['DELETE'])
def api_revoke_user_permission(permission_id):
    """
    JSON API to soft-revoke an organization permission.
    """
    client = get_supabase_client()
    try:
        user_info = check_admin(client)
        admin_profile_id = user_info["profile_id"]
    except Exception as e:
        return jsonify({"error": str(e)}), 403
        
    try:
        # Fetch the permission record
        perm_res = client.table('organization_permission').select('*').eq('id', permission_id).execute()
        if not perm_res.data:
            return jsonify({"error": "Permission record not found"}), 404
        perm = perm_res.data[0]
        
        if perm.get('status') != 'Active':
            return jsonify({"error": "Permission is not active"}), 400
            
        # Get target user email
        target_user = client.table('user_profile').select('email').eq('id', perm['user_id']).execute()
        user_email = target_user.data[0].get('email') if target_user.data else 'Unknown'
        
        # Get organization name
        org = client.table('organization').select('organization_name').eq('id', perm['organization_id']).execute()
        org_name = org.data[0].get('organization_name') if org.data else 'Unknown'
        
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        res = client.table('organization_permission').update({
            'status': 'Revoked',
            'revoked_at': now,
            'revoked_by_user_id': admin_profile_id
        }).eq('id', permission_id).execute()
        
        if not res.data:
            raise ValueError("Failed to revoke permission record")
            
        updated_perm = res.data[0]
        
        # Log audit event
        from project_funding_ledger.audit import log_audit_event_async
        log_audit_event_async(
            user_id=user_info["user"].id,
            action_type='Permission Change',
            entity_type='User',
            table_name='organization_permission',
            record_id=permission_id,
            related_organization_id=perm['organization_id'],
            old_value=perm,
            new_value=updated_perm,
            summary=f"Admin revoked permission for user {user_email} from organization '{org_name}'."
        )
        
        return jsonify(updated_perm), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


