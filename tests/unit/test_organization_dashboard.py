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

@patch("project_funding_ledger.supabase_client.create_client")
def test_login_redirect_single_org(mock_create_client, client):
    """
    Test that a logged-in user with permission for exactly 1 organization is redirected to the details page.
    """
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client
    
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "stakeholder@example.com"
    mock_user.user_metadata = {"full_name": "Test Stakeholder"}
    mock_client.auth.sign_in_with_password.return_value = MagicMock(
        session=MagicMock(access_token="tok", refresh_token="ref"),
        user=mock_user
    )

    def mock_table_routing(table_name):
        mock_tbl = MagicMock()
        if table_name == 'user_profile':
            mock_tbl.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"id": "prof-123", "user_type": "Organization Stakeholder"}]
            )
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data={"id": "prof-123", "user_type": "Organization Stakeholder"}
            )
        elif table_name == 'organization_permission':
            mock_tbl.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"organization_id": "org-uuid-single"}]
            )
        return mock_tbl

    mock_client.table.side_effect = mock_table_routing

    response = client.post('/login', data={
        "email": "stakeholder@example.com",
        "password": "password123"
    }, follow_redirects=False)

    assert response.status_code == 302
    assert "/organizations/org-uuid-single" in response.headers["Location"]


@patch("project_funding_ledger.supabase_client.create_client")
def test_login_redirect_multiple_orgs(mock_create_client, client):
    """
    Test that a logged-in user with 2+ permitted organizations is redirected to the dashboard.
    """
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client
    
    mock_user = MagicMock()
    mock_user.id = "user-456"
    mock_user.email = "pm@example.com"
    mock_user.user_metadata = {"full_name": "Test PM"}
    mock_client.auth.sign_in_with_password.return_value = MagicMock(
        session=MagicMock(access_token="tok", refresh_token="ref"),
        user=mock_user
    )

    def mock_table_routing(table_name):
        mock_tbl = MagicMock()
        if table_name == 'user_profile':
            mock_tbl.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"id": "prof-456", "user_type": "Program Manager"}]
            )
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data={"id": "prof-456", "user_type": "Program Manager"}
            )
        elif table_name == 'organization_permission':
            mock_tbl.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"organization_id": "org-1"}, {"organization_id": "org-2"}]
            )
        return mock_tbl

    mock_client.table.side_effect = mock_table_routing

    response = client.post('/login', data={
        "email": "pm@example.com",
        "password": "password123"
    }, follow_redirects=False)

    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


@patch("project_funding_ledger.supabase_client.create_client")
def test_api_my_organizations(mock_create_client, client):
    """
    Test GET /api/my-organizations returns permitted organizations for authenticated user.
    """
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client

    mock_user_res = MagicMock()
    mock_user_res.user.id = "user-789"
    mock_client.auth.get_user.return_value = mock_user_res

    mock_profile = {"id": "prof-789", "user_type": "Organization Stakeholder"}
    mock_perm = [{
        "permission_level": "View",
        "organization": {
            "id": "org-789",
            "organization_name": "Alpha Org",
            "organization_slug": "alpha-org",
            "status": "Active",
            "organization_type": "Fiscal Sponsorship"
        }
    }]

    def mock_table_routing(table_name):
        mock_tbl = MagicMock()
        if table_name == 'user_profile':
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=mock_profile)
        elif table_name == 'organization_permission':
            mock_tbl.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=mock_perm)
        return mock_tbl

    mock_client.table.side_effect = mock_table_routing

    response = client.get('/api/my-organizations')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["organization_name"] == "Alpha Org"
    assert data[0]["permission_level"] == "View"


@patch("project_funding_ledger.supabase_client.create_client")
def test_api_organization_detail_unauthorized(mock_create_client, client):
    """
    Test GET /api/organizations/<org_id> returns 403 when user does not have permission.
    """
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client

    mock_user_res = MagicMock()
    mock_user_res.user.id = "user-999"
    mock_client.auth.get_user.return_value = mock_user_res

    mock_profile = {"id": "prof-999", "user_type": "Organization Stakeholder"}

    def mock_table_routing(table_name):
        mock_tbl = MagicMock()
        if table_name == 'user_profile':
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=mock_profile)
        elif table_name == 'organization_permission':
            mock_tbl.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        return mock_tbl

    mock_client.table.side_effect = mock_table_routing

    response = client.get('/api/organizations/forbidden-org-id')
    assert response.status_code == 403
    assert "Permission denied" in response.get_json()["error"]


@patch("project_funding_ledger.supabase_client.create_client")
def test_api_update_organization_program_manager(mock_create_client, client):
    """
    Test PUT /api/organizations/<org_id> allows Program Manager to edit org metadata.
    """
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client

    mock_user_res = MagicMock()
    mock_user_res.user.id = "pm-user-1"
    mock_client.auth.get_user.return_value = mock_user_res

    mock_profile = {"id": "pm-prof-1", "user_type": "Program Manager"}

    def mock_table_routing(table_name):
        mock_tbl = MagicMock()
        if table_name == 'user_profile':
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=mock_profile)
        elif table_name == 'organization_permission':
            mock_tbl.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"permission_level": "Edit Metadata"}]
            )
        elif table_name == 'organization':
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data={"id": "org-pm-1", "organization_name": "Old Name"}
            )
            mock_tbl.update.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"id": "org-pm-1", "organization_name": "New Updated Name", "status": "Active"}]
            )
        return mock_tbl

    mock_client.table.side_effect = mock_table_routing

    response = client.put('/api/organizations/org-pm-1', json={
        "organization_name": "New Updated Name"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["organization_name"] == "New Updated Name"
