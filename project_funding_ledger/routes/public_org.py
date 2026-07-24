import os
from flask import Blueprint, render_template, current_app
from project_funding_ledger.supabase_client import get_supabase_client

public_org_bp = Blueprint('public_org', __name__)

@public_org_bp.route('/organizations')
def organization_list():
    client = get_supabase_client()
    try:
        res = client.table('organization').select(
            'organization_name, organization_slug, description, website_url, donation_url, source_code_url, organization_type, join_date, status'
        ).order('organization_name').execute()
        organizations = res.data or []
    except Exception as e:
        current_app.logger.exception('Failed to load public organizations')
        raise
    return render_template('organization_list.html', organizations=organizations)

