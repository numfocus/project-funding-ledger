import os
from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from project_funding_ledger.auth import auth_bp
from project_funding_ledger.profile import profile_bp
from project_funding_ledger.supabase_client import save_supabase_session
from project_funding_ledger.queue.webhooks import tasks_bp
from project_funding_ledger.routes.org_import import org_import_bp
from project_funding_ledger.routes.public_org import public_org_bp

# Load environment variables from .env file
load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure Flask session secret key
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY')
    
    # Fallback secret key for local development and debug modes
    if not app.config['SECRET_KEY']:
        if app.debug or os.environ.get('FLASK_DEBUG') == '1':
            app.config['SECRET_KEY'] = 'dev-secret-key-123456789'
        else:
            raise ValueError("No SECRET_KEY set in production environment")

    os.makedirs(app.instance_path, exist_ok=True)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(org_import_bp)
    app.register_blueprint(public_org_bp)


    # After-request hook to persist refreshed Supabase tokens in session cookie
    app.after_request(save_supabase_session)

    @app.route('/')
    def index():
        # Redirect index to admin dashboard if System Administrator, else profile page
        from project_funding_ledger.supabase_client import get_supabase_client
        client = get_supabase_client()
        try:
            user_res = client.auth.get_user()
            user = user_res.user if user_res else None
            if user:
                profile_res = client.table('user_profile').select('user_type').eq('auth_user_id', user.id).execute()
                if profile_res.data and profile_res.data[0].get('user_type') == 'System Administrator':
                    return redirect(url_for('org_import.admin_dashboard'))
        except Exception:
            pass
        return redirect(url_for('profile.profile_page'))

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
