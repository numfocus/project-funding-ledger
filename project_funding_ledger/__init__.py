import os
import flask
from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from project_funding_ledger.auth import auth_bp
import project_funding_ledger.exceptions
from project_funding_ledger.profile import profile_bp
from project_funding_ledger.supabase_client import save_supabase_session
from project_funding_ledger.queue.webhooks import tasks_bp
from project_funding_ledger.routes.org_import import org_import_bp
from project_funding_ledger.routes.organization import org_bp
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
    app.register_blueprint(org_bp)
    app.register_blueprint(public_org_bp)

    # After-request hook to persist refreshed Supabase tokens in session cookie
    app.after_request(save_supabase_session)

    @app.route('/')
    def index():
        return redirect(url_for('public_org.organization_list'))

    @app.errorhandler(project_funding_ledger.exceptions.AuthRequiredError)
    def auth_required(error):
        # TODO(tswast): allow auth.login to redirect to the desired page, with protections to avoid redirecting off of the current site.
        return redirect(url_for('auth.login'))

    return app
