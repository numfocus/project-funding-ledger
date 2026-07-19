import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def app():
    from project_funding_ledger import create_app
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key"
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@patch('project_funding_ledger.auth.get_supabase_client')
def test_register_get_step1(mock_get_supabase, client):
    # Verify GET /register without email renders check invite step
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Enter Invited Email" in response.data

@patch('project_funding_ledger.auth.get_supabase_client')
def test_register_check_invite_success(mock_get_supabase, client):
    # Mock supabase client RPC to return True (invited)
    mock_client = MagicMock()
    mock_get_supabase.return_value = mock_client
    mock_client.rpc.return_value.execute.return_value.data = True
    
    response = client.post('/register', data={
        'action': 'check_invite',
        'email': 'invited@example.com'
    })
    
    # Verify redirect to register with email parameter
    assert response.status_code == 302
    assert 'email=invited@example.com' in response.location

@patch('project_funding_ledger.auth.get_supabase_client')
def test_register_check_invite_failure(mock_get_supabase, client):
    # Mock supabase client RPC to return False (not invited)
    mock_client = MagicMock()
    mock_get_supabase.return_value = mock_client
    mock_client.rpc.return_value.execute.return_value.data = False
    
    response = client.post('/register', data={
        'action': 'check_invite',
        'email': 'not_invited@example.com'
    })
    
    assert response.status_code == 200
    assert b"This email address is not invited or has already been registered." in response.data

@patch('project_funding_ledger.auth.get_supabase_client')
def test_register_complete_registration_success(mock_get_supabase, client):
    mock_client = MagicMock()
    mock_get_supabase.return_value = mock_client
    
    # Mock verification RPC to return True
    mock_client.rpc.return_value.execute.return_value.data = True
    
    # Mock sign_up success (with session)
    mock_user = MagicMock()
    mock_user.id = 'test-user-id'
    mock_session = MagicMock()
    mock_session.access_token = 'access'
    mock_session.refresh_token = 'refresh'
    
    mock_signup_res = MagicMock()
    mock_signup_res.user = mock_user
    mock_signup_res.session = mock_session
    mock_client.auth.sign_up.return_value = mock_signup_res
    
    # Mock user_profile query success
    mock_profile_data = [{'id': 'profile-id', 'user_type': 'Organization Stakeholder'}]
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_profile_data
    
    with patch('project_funding_ledger.auth.log_audit_event') as mock_log:
        response = client.post('/register', data={
            'action': 'complete_registration',
            'email': 'invited@example.com',
            'full_name': 'Invited User',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        
        # Verify redirect to profile page (since we automatically log in on success)
        assert response.status_code == 302
        assert response.location.endswith('/profile')
        assert mock_log.called
