import os
from flask import g, session
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """
    Returns a request-scoped Supabase client.
    If the current session contains authentication tokens, restores the session.
    """
    if 'supabase_client' not in g:
        url = os.environ.get("SUPABASE_URL", "http://127.0.0.1:54321")
        # Try a few common environment variable names for the anon key
        key = os.environ.get("SUPABASE_PUBLISHABLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
        
        if not key:
            # For local debugging, fallback to checking if we are in debug mode,
            # but raise a helpful error otherwise
            raise ValueError(
                "SUPABASE_PUBLISHABLE_KEY (or SUPABASE_ANON_KEY) is not set in environment variables. "
                "Please configure it in a .env file."
            )
            
        g.supabase_client = create_client(url, key)
        
        # Restore user session if tokens exist in the secure Flask session cookie
        access_token = session.get("access_token")
        refresh_token = session.get("refresh_token")
        if access_token and refresh_token:
            try:
                g.supabase_client.auth.set_session(access_token, refresh_token)
            except Exception:
                # Token refresh might have failed (e.g. if the local supabase container was reset).
                # Clear invalid session tokens.
                session.pop("access_token", None)
                session.pop("refresh_token", None)
                
    return g.supabase_client

def save_supabase_session(response):
    """
    After-request hook to save any updated/refreshed tokens from the Supabase client
    back into the Flask session cookie.
    """
    if 'supabase_client' in g:
        try:
            sb_session = g.supabase_client.auth.get_session()
            if sb_session:
                session["access_token"] = sb_session.access_token
                session["refresh_token"] = sb_session.refresh_token
            else:
                session.pop("access_token", None)
                session.pop("refresh_token", None)
        except Exception:
            pass
    return response
