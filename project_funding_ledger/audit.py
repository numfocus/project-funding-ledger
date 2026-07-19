from flask import request, has_request_context
from supabase import Client

def log_audit_event(client: Client, user_id: str, action_type: str, entity_type: str, summary: str, 
                    table_name: str = None, record_id: str = None, related_organization_id: str = None, 
                    related_funding_source_id: str = None, old_value: dict = None, new_value: dict = None):
    """
    Helper function to log a significant application activity to the audit_log table.
    Ensures that IP address and User Agent are populated if in a Flask request context.
    Does not let errors crash the main application flow.
    """
    try:
        ip_address = None
        user_agent = None
        if has_request_context():
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent')
            
        audit_data = {
            'user_id': user_id,
            'action_type': action_type,
            'entity_type': entity_type,
            'table_name': table_name,
            'record_id': record_id,
            'related_organization_id': related_organization_id,
            'related_funding_source_id': related_funding_source_id,
            'summary': summary,
            'old_value': old_value,
            'new_value': new_value,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        client.table('audit_log').insert(audit_data).execute()
    except Exception as e:
        # Prevent audit logging issues from failing the user's primary action,
        # but print/log the exception for debug purposes.
        print(f"Error writing audit log: {str(e)}")
