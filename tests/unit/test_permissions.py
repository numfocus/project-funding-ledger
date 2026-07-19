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
def test_api_user_permissions_success(mock_create_client, client):
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client
    
    # Mock admin auth session/user
    mock_user_res = MagicMock()
    mock_user_res.user.id = "admin-user-id"
    mock_client.auth.get_user.return_value = mock_user_res
    
    # Mock check_admin profile check
    mock_profile_data = {"id": "admin-profile-id", "user_type": "System Administrator"}
    
    # Mock permission query results
    mock_perm_data = [
        {
            "id": "perm-id-123",
            "user_id": "target-user-id",
            "organization_id": "org-id-456",
            "permission_level": "Manage",
            "status": "Active",
            "organization": {"organization_name": "Test Org"}
        }
    ]
    
    # Setup routing for tables
    def mock_table_routing(table_name):
        mock_tbl = MagicMock()
        if table_name == 'user_profile':
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=mock_profile_data)
        elif table_name == 'organization_permission':
            mock_tbl.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=mock_perm_data)
        return mock_tbl
        
    mock_client.table.side_effect = mock_table_routing
    
    response = client.get("/api/admin/users/target-user-id/permissions")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["id"] == "perm-id-123"
    assert data[0]["organization"]["organization_name"] == "Test Org"


@patch("project_funding_ledger.supabase_client.create_client")
@patch("project_funding_ledger.queue.get_queue_client")
def test_api_grant_user_permission_success(mock_get_queue, mock_create_client, client):
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client
    
    # Mock admin auth session/user
    mock_user_res = MagicMock()
    mock_user_res.user.id = "admin-user-id"
    mock_client.auth.get_user.return_value = mock_user_res
    
    # Mock table routing
    def mock_table_routing(table_name):
        mock_tbl = MagicMock()
        if table_name == 'user_profile':
            # check_admin profile lookup
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"id": "admin-profile-id", "user_type": "System Administrator"})
            # target user check lookup
            mock_tbl.select.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock(data=[{"id": "target-user-id", "email": "target@example.com"}])
        elif table_name == 'organization':
            mock_tbl.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "org-id-456", "organization_name": "Test Org"}])
        elif table_name == 'organization_permission':
            # existing check
            mock_tbl.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
            # insert
            mock_tbl.insert.return_value.execute.return_value = MagicMock(data=[{
                "id": "new-perm-id",
                "user_id": "target-user-id",
                "organization_id": "org-id-456",
                "permission_level": "Manage",
                "status": "Active"
            }])
        return mock_tbl
        
    mock_client.table.side_effect = mock_table_routing
    
    response = client.post("/api/admin/users/target-user-id/permissions", json={
        "organization_id": "org-id-456",
        "permission_level": "Manage"
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == "new-perm-id"
    assert data["permission_level"] == "Manage"


@patch("project_funding_ledger.supabase_client.create_client")
@patch("project_funding_ledger.queue.get_queue_client")
def test_api_revoke_user_permission_success(mock_get_queue, mock_create_client, client):
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client
    
    # Mock admin auth session/user
    mock_user_res = MagicMock()
    mock_user_res.user.id = "admin-user-id"
    mock_client.auth.get_user.return_value = mock_user_res
    
    # Mock table routing
    def mock_table_routing(table_name):
        mock_tbl = MagicMock()
        if table_name == 'user_profile':
            # check_admin profile lookup
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.side_effect = [
                MagicMock(data={"id": "admin-profile-id", "user_type": "System Administrator"})
            ]
            # target user email lookup
            mock_tbl.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"email": "target@example.com"}])
        elif table_name == 'organization':
            mock_tbl.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"organization_name": "Test Org"}])
        elif table_name == 'organization_permission':
            # perm select
            mock_tbl.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{
                "id": "perm-id-123",
                "user_id": "target-user-id",
                "organization_id": "org-id-456",
                "permission_level": "Manage",
                "status": "Active"
            }])
            # perm update
            mock_tbl.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{
                "id": "perm-id-123",
                "status": "Revoked"
            }])
        return mock_tbl
        
    mock_client.table.side_effect = mock_table_routing
    
    response = client.delete("/api/admin/users/permissions/perm-id-123")
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "Revoked"
