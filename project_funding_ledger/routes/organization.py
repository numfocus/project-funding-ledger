import os
import uuid
import datetime
from flask import Blueprint, request, jsonify, abort, render_template, redirect, url_for, flash
from werkzeug.exceptions import HTTPException
from project_funding_ledger.supabase_client import get_supabase_client

org_bp = Blueprint('org', __name__)

def check_user_auth(client):
    """
    Checks if the user in the current Supabase context is authenticated.
    Returns (user, user_profile) tuple or (None, None).
    """
    try:
        user_res = client.auth.get_user()
        if not user_res or not user_res.user:
            return None, None
        user = user_res.user
        profile_res = client.table('user_profile').select('*').eq('auth_user_id', user.id).single().execute()
        if not profile_res.data:
            return user, None
        return user, profile_res.data
    except Exception:
        return None, None

def get_permitted_organizations(client, user_profile):
    """
    Fetches the list of organizations the given user profile is permitted to access.
    System Administrators receive all active organizations.
    Other users receive organizations with an Active entry in organization_permission.
    """
    if not user_profile:
        return []

    user_type = user_profile.get('user_type')
    if user_type == 'System Administrator':
        res = client.table('organization').select('*').is_('deleted_at', 'null').order('organization_name').execute()
        orgs = res.data or []
        for org in orgs:
            org['permission_level'] = 'Manage'
        return orgs

    # Non-admin users: query active permissions
    perms_res = client.table('organization_permission') \
        .select('permission_level, organization:organization_id(*)') \
        .eq('user_id', user_profile['id']) \
        .eq('status', 'Active') \
        .execute()

    orgs = []
    for perm in (perms_res.data or []):
        org = perm.get('organization')
        if org and org.get('deleted_at') is None:
            org['permission_level'] = perm.get('permission_level')
            orgs.append(org)

    orgs.sort(key=lambda x: x.get('organization_name', '').lower())
    return orgs

def check_organization_permission(client, user_profile, org_id):
    """
    Checks if the user has access to a specific org_id.
    Returns (has_access, permission_level).
    """
    if not user_profile:
        return False, None

    if user_profile.get('user_type') == 'System Administrator':
        return True, 'Manage'

    perms_res = client.table('organization_permission') \
        .select('permission_level') \
        .eq('user_id', user_profile['id']) \
        .eq('organization_id', org_id) \
        .eq('status', 'Active') \
        .execute()

    if perms_res.data and len(perms_res.data) > 0:
        return True, perms_res.data[0].get('permission_level')
    
    return False, None


@org_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Renders the My Orgs dashboard page.
    """
    client = get_supabase_client()
    user, profile = check_user_auth(client)
    if not user or not profile:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('auth.login'))

    return render_template('dashboard.html', user_profile=profile)


@org_bp.route('/organizations/<org_id>', methods=['GET'])
def org_detail(org_id):
    """
    Renders the Organization Details page for authorized users.
    """
    client = get_supabase_client()
    user, profile = check_user_auth(client)
    if not user or not profile:
        flash("Please log in to view organization details.", "warning")
        return redirect(url_for('auth.login'))

    has_access, perm_level = check_organization_permission(client, profile, org_id)
    if not has_access:
        flash("You do not have permission to view this organization.", "error")
        return redirect(url_for('org.dashboard'))

    # Fetch org details
    try:
        org_res = client.table('organization').select('*').eq('id', org_id).single().execute()
        org = org_res.data if org_res else None
        if not org or org.get('deleted_at') is not None:
            flash("Organization not found.", "error")
            return redirect(url_for('org.dashboard'))
    except Exception as e:
        flash(f"Error fetching organization details: {str(e)}", "error")
        return redirect(url_for('org.dashboard'))

    return render_template('org_detail.html', user_profile=profile, organization=org, permission_level=perm_level)


@org_bp.route('/api/my-organizations', methods=['GET'])
def api_my_organizations():
    """
    API returning the list of organizations the authenticated user has access to.
    """
    client = get_supabase_client()
    user, profile = check_user_auth(client)
    if not user or not profile:
        return jsonify({"error": "Authentication required"}), 401

    orgs = get_permitted_organizations(client, profile)
    return jsonify(orgs), 200


@org_bp.route('/api/organizations/<org_id>', methods=['GET'])
def api_get_organization(org_id):
    """
    API returning a single organization details if authorized.
    """
    client = get_supabase_client()
    user, profile = check_user_auth(client)
    if not user or not profile:
        return jsonify({"error": "Authentication required"}), 401

    has_access, perm_level = check_organization_permission(client, profile, org_id)
    if not has_access:
        return jsonify({"error": "Permission denied"}), 403

    try:
        org_res = client.table('organization').select('*').eq('id', org_id).single().execute()
        if not org_res.data or org_res.data.get('deleted_at') is not None:
            return jsonify({"error": "Organization not found"}), 404
        
        data = org_res.data
        data['permission_level'] = perm_level
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@org_bp.route('/api/organizations', methods=['POST'])
def api_create_organization():
    """
    API to create a new organization (Program Managers & System Administrators).
    """
    client = get_supabase_client()
    user, profile = check_user_auth(client)
    if not user or not profile:
        return jsonify({"error": "Authentication required"}), 401

    user_type = profile.get('user_type')
    if user_type not in ['System Administrator', 'Program Manager']:
        return jsonify({"error": "Creating an organization requires Program Manager or Admin privileges"}), 403

    data = request.json or {}
    organization_name = (data.get('organization_name') or '').strip()
    organization_slug = (data.get('organization_slug') or '').strip().lower()
    organization_type = data.get('organization_type', 'Fiscal Sponsorship')
    status = data.get('status', 'Active')
    description = data.get('description', '')
    website_url = data.get('website_url', '')
    source_code_url = data.get('source_code_url', '')
    donation_url = data.get('donation_url', '')
    join_date = data.get('join_date') or datetime.date.today().isoformat()

    if not organization_name or not organization_slug:
        return jsonify({"error": "Organization Name and Organization Slug are required"}), 400

    valid_types = ['Fiscal Sponsorship', 'Event']
    valid_statuses = ['Active', 'Inactive', 'Archived', 'Dormant', 'Closed']
    if organization_type not in valid_types:
        return jsonify({"error": f"Invalid type. Must be one of: {', '.join(valid_types)}"}), 400
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    try:
        # Check duplicate slug
        existing_slug = client.table('organization').select('id').eq('organization_slug', organization_slug).execute()
        if existing_slug.data:
            return jsonify({"error": f"Organization with slug '{organization_slug}' already exists."}), 400

        # 1. Insert key
        import_key = organization_slug
        key_res = client.table('organization_key').insert({
            'import_key': import_key,
            'created_by_user_id': profile['id'],
            'updated_by_user_id': profile['id']
        }).execute()
        
        if not key_res.data:
            raise ValueError("Failed to create organization_key record")
        
        org_id = key_res.data[0]['id']

        # 2. Insert organization
        org_res = client.table('organization').insert({
            'id': org_id,
            'organization_name': organization_name,
            'organization_slug': organization_slug,
            'status': status,
            'organization_type': organization_type,
            'description': description,
            'website_url': website_url,
            'source_code_url': source_code_url,
            'donation_url': donation_url,
            'join_date': join_date,
            'created_by_user_id': profile['id'],
            'updated_by_user_id': profile['id']
        }).execute()

        if not org_res.data:
            raise ValueError("Failed to create organization record")

        new_org = org_res.data[0]

        # 3. Insert organization_internal default
        client.table('organization_internal').insert({
            'id': org_id,
            'created_by_user_id': profile['id'],
            'updated_by_user_id': profile['id']
        }).execute()

        # 4. If created by Program Manager, automatically grant them 'Manage' permission to the new org
        if user_type == 'Program Manager':
            client.table('organization_permission').insert({
                'user_id': profile['id'],
                'organization_id': org_id,
                'permission_level': 'Manage',
                'status': 'Active',
                'created_by_user_id': profile['id']
            }).execute()

        # Audit log
        from project_funding_ledger.audit import log_audit_event_async
        log_audit_event_async(
            user_id=user.id,
            action_type='Create',
            entity_type='Organization',
            table_name='organization',
            record_id=org_id,
            new_value=new_org,
            summary=f"User created Organization '{organization_name}'."
        )

        return jsonify(new_org), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@org_bp.route('/api/organizations/<org_id>', methods=['PUT'])
def api_update_organization(org_id):
    """
    API to update an existing organization (Program Managers or Users with Edit Metadata/Manage perm).
    """
    client = get_supabase_client()
    user, profile = check_user_auth(client)
    if not user or not profile:
        return jsonify({"error": "Authentication required"}), 401

    has_access, perm_level = check_organization_permission(client, profile, org_id)
    if not has_access or (perm_level == 'View' and profile.get('user_type') != 'Program Manager'):
        return jsonify({"error": "Permission denied: edit access required"}), 403

    data = request.json or {}
    update_data = {}
    if 'organization_name' in data:
        update_data['organization_name'] = data['organization_name'].strip()
    if 'status' in data:
        update_data['status'] = data['status']
    if 'organization_type' in data:
        update_data['organization_type'] = data['organization_type']
    if 'description' in data:
        update_data['description'] = data['description']
    if 'website_url' in data:
        update_data['website_url'] = data['website_url']
    if 'source_code_url' in data:
        update_data['source_code_url'] = data['source_code_url']
    if 'donation_url' in data:
        update_data['donation_url'] = data['donation_url']

    if not update_data:
        return jsonify({"error": "No update fields provided"}), 400

    update_data['updated_by_user_id'] = profile['id']

    try:
        old_org_res = client.table('organization').select('*').eq('id', org_id).single().execute()
        old_org = old_org_res.data if old_org_res else {}

        res = client.table('organization').update(update_data).eq('id', org_id).execute()
        if not res.data:
            return jsonify({"error": "Failed to update organization"}), 500

        updated_org = res.data[0]

        # Audit log
        from project_funding_ledger.audit import log_audit_event_async
        log_audit_event_async(
            user_id=user.id,
            action_type='Update',
            entity_type='Organization',
            table_name='organization',
            record_id=org_id,
            old_value=old_org,
            new_value=updated_org,
            summary=f"User updated Organization metadata for '{updated_org.get('organization_name')}'."
        )

        return jsonify(updated_org), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
