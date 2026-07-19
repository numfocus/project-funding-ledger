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

def log_audit_event_async(user_id: str, action_type: str, entity_type: str, summary: str, 
                           table_name: str = None, record_id: str = None, related_organization_id: str = None, 
                           related_funding_source_id: str = None, old_value: dict = None, new_value: dict = None):
    """
    Enqueues an audit event to be logged asynchronously in the background.
    Captures current Flask request context metadata (IP, User-Agent, user session tokens).
    If the queue client is not available or fails, falls back to synchronous execution.
    """
    from flask import request, session, has_request_context
    from project_funding_ledger.queue import get_queue_client
    
    ip_address = None
    user_agent = None
    access_token = None
    refresh_token = None
    
    if has_request_context():
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        # Retrieve user auth session tokens from secure cookie
        access_token = session.get("access_token")
        refresh_token = session.get("refresh_token")
        
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
    
    try:
        queue = get_queue_client()
        queue.enqueue("log_audit_event", audit_data=audit_data, access_token=access_token, refresh_token=refresh_token)
    except Exception as e:
        # Prevent logging subsystem failures from crashing the main flow.
        # Fall back to synchronous logging so audit integrity is maintained.
        print(f"Error enqueuing audit log, falling back to sync: {str(e)}")
        try:
            from project_funding_ledger.supabase_client import get_supabase_client
            log_audit_event(
                client=get_supabase_client(),
                user_id=user_id,
                action_type=action_type,
                entity_type=entity_type,
                summary=summary,
                table_name=table_name,
                record_id=record_id,
                related_organization_id=related_organization_id,
                related_funding_source_id=related_funding_source_id,
                old_value=old_value,
                new_value=new_value
            )
        except Exception as sync_e:
            print(f"Sync fallback audit logging failed: {str(sync_e)}")

