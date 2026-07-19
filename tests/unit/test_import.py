import os
import datetime
import pytest
from unittest.mock import MagicMock, patch

from project_funding_ledger.queue.tasks import process_organization_import_task, confirm_organization_import_row_task

@patch("openpyxl.load_workbook")
@patch("supabase.create_client")
def test_process_organization_import_new_and_update(mock_create_client, mock_load_workbook):
    # Setup mock supabase client
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    
    # Mock supabase responses
    # First, for ORG-NEW key check: return empty data
    # Second, for ORG-EXIST key check: return existing key record
    # Third, for ORG-IDENTICAL key check: return existing key record
    mock_key_select = MagicMock()
    mock_key_select.execute.side_effect = [
        MagicMock(data=[]), # ORG-NEW
        MagicMock(data=[{"id": "existing-uuid-123", "import_key": "ORG-EXIST"}]), # ORG-EXIST
        MagicMock(data=[{"id": "existing-uuid-456", "import_key": "ORG-IDENTICAL"}]) # ORG-IDENTICAL
    ]
    
    # Mock existing organization table records for updates comparison
    mock_org_select = MagicMock()
    mock_org_select.execute.side_effect = [
        # ORG-EXIST org & internal
        MagicMock(data={"organization_name": "Exist Org Name", "organization_slug": "exist-org-slug-old", "description": "Old desc"}),
        MagicMock(data={"overhead_grant": 0.10, "overhead_donation_general": 0.08, "overhead_donation_corporate": 0.05, "notes": "Old notes"}),
        # ORG-IDENTICAL org & internal (exactly matches the row values)
        MagicMock(data={"organization_name": "Identical Org Name", "organization_slug": "identical-org-slug", "description": "Identical desc", "website_url": "https://identical.org", "source_code_url": "https://github.com/identical", "donation_url": "https://donate.identical.org", "join_date": "2025-01-01", "organization_type": "Event"}),
        MagicMock(data={"overhead_grant": 0.10, "overhead_donation_general": 0.08, "overhead_donation_corporate": 0.05, "notes": "Identical notes"})
    ]
    
    # Configure mock client behavior based on table name
    mock_tables = {}
    def mock_table_routing(table_name):
        if table_name not in mock_tables:
            mock_tables[table_name] = MagicMock()
        mock_tbl = mock_tables[table_name]
        if table_name == 'organization_key':
            mock_tbl.select.return_value.eq.return_value = mock_key_select
        elif table_name == 'organization':
            mock_tbl.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute = mock_org_select.execute
        elif table_name == 'organization_internal':
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute = mock_org_select.execute
        return mock_tbl
        
    mock_client.table.side_effect = mock_table_routing

    # Setup mock openpyxl workbook and sheet
    mock_wb = MagicMock()
    mock_sheet = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_wb.active = mock_sheet
    
    mock_row_data = [
        # Headers
        ("Organization_PFL_Key", "Organization Name", "Organziation Slug", "Description", "github page", "Project Website", "Donation Link", "Join Date", "Contacts", "Governing Agreements", "Reporting Obligations", "Documents", "Type", "Grant Overhead", "General Donation Overhead", "Corporate Donation Overhead", "Internal Notes"),
        # Row 1: New
        ("ORG-NEW", "New Org Name", "new-org-slug", "A new org desc", "https://github.com/neworg", "https://neworg.org", "https://donate.neworg.org", "2026-01-01", "", "", "", "", "Fiscal Sponsorship", "10%", "15.0", 5, "Some notes"),
        # Row 2: Update with diffs (slug changes)
        ("ORG-EXIST", "Exist Org Name", "exist-org-slug-new", "Old desc", "https://github.com/existorg", "https://existorg.org", "https://donate.existorg.org", "2025-01-01", "", "", "", "", "Event", "10.0", "8.0", 5, "Old notes"),
        # Row 3: Update with zero diffs (matches DB exactly)
        ("ORG-IDENTICAL", "Identical Org Name", "identical-org-slug", "Identical desc", "https://github.com/identical", "https://identical.org", "https://donate.identical.org", "2025-01-01", "", "", "", "", "Event", "10.0", "8.0", 5, "Identical notes")
    ]
    mock_sheet.iter_rows.return_value = mock_row_data
    
    # Run task
    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove:
        process_organization_import_task("dummy_path.xlsx", "batch-123")
        
        # Verify Excel workbook was loaded
        mock_load_workbook.assert_called_once_with("dummy_path.xlsx", read_only=True, data_only=True)
        # Verify file was cleaned up at the end
        mock_remove.assert_called_once_with("dummy_path.xlsx")
            
        # Check that we staged three rows
        insert_mock = mock_tables['organization_import_row'].insert
        assert insert_mock.call_count == 3
        
        insert_calls = insert_mock.call_args_list
        # Row 1 (ORG-NEW) -> Pending
        assert insert_calls[0][0][0]["import_key"] == "ORG-NEW"
        assert insert_calls[0][0][0]["status"] == "Pending"
        
        # Row 2 (ORG-EXIST) -> Pending (has changes)
        assert insert_calls[1][0][0]["import_key"] == "ORG-EXIST"
        assert insert_calls[1][0][0]["status"] == "Pending"
        
        # Row 3 (ORG-IDENTICAL) -> Confirmed (matches DB exactly)
        assert insert_calls[2][0][0]["import_key"] == "ORG-IDENTICAL"
        assert insert_calls[2][0][0]["status"] == "Confirmed"

@patch("supabase.create_client")
def test_confirm_organization_import_row_create(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    
    # Mock staging row query response for action_type = 'Create'
    mock_row_data = {
        "id": "row-123",
        "batch_id": "batch-123",
        "import_key": "ORG-NEW",
        "action_type": "Create",
        "status": "Pending",
        "organization_data": {
            "organization_name": "New Org",
            "organization_slug": "new-org",
            "status": "Active",
            "organization_type": "Fiscal Sponsorship",
            "description": "Desc",
            "website_url": "http://org.org",
            "overhead_grant": 0.10,
            "overhead_donation_general": 0.12,
            "overhead_donation_corporate": 0.05,
            "notes": "Notes"
        }
    }
    
    # Configure mock responses for select, insert, and update
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=mock_row_data)

    
    # Mock organization_key insert response (returns UUID id)
    mock_client.table.return_value.insert.side_effect = [
        MagicMock(data=[{"id": "new-org-uuid"}]), # org_key insert
        MagicMock(data=[]), # org insert
        MagicMock(data=[])  # org_internal insert
    ]
    
    # Run confirmation task
    confirm_organization_import_row_task("row-123")
    
    # Verify staging status is updated to Confirmed
    mock_client.table.return_value.update.assert_called_once()
    mock_client.table.return_value.update.return_value.eq.assert_called_once_with('id', 'row-123')


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
def test_import_routes_auth_check(mock_create_client, client):
    # Setup mock supabase client returning non-admin user
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client
    
    # Mock user_res
    mock_user_res = MagicMock()
    mock_user_res.user.id = "user-id-123"
    mock_client.auth.get_user.return_value = mock_user_res
    
    # Mock profile response (User is not admin, so access should be denied)
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"user_type": "Organization Stakeholder"})
    
    # Attempting to hit the route should return 403 Forbidden
    response = client.post("/admin/import/organizations")
    assert response.status_code == 403


@patch("project_funding_ledger.supabase_client.create_client")
def test_admin_dashboard_unauthorized_redirect(mock_create_client, client):
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client
    
    # Mock user_res returning None (unauthenticated)
    mock_client.auth.get_user.return_value = None
    
    # Get dashboard should redirect to login
    response = client.get("/admin/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


@patch("project_funding_ledger.supabase_client.create_client")
def test_api_organizations_success(mock_create_client, client):
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client
    
    # Mock user_res returning admin
    mock_user_res = MagicMock()
    mock_user_res.user.id = "admin-id"
    mock_client.auth.get_user.return_value = mock_user_res
    
    # Mock admin role check
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"user_type": "System Administrator"})
    
    # Setup routing for tables
    mock_org_list = MagicMock()
    mock_org_list.execute.return_value = MagicMock(data=[
        {"id": "org-uuid-1", "organization_name": "Test Org", "organization_slug": "test-org"}
    ])
    
    mock_internal_list = MagicMock()
    mock_internal_list.execute.return_value = MagicMock(data=[
        {"id": "org-uuid-1", "overhead_grant": 0.1}
    ])
    
    def mock_table_routing(table_name):
        mock_tbl = MagicMock()
        if table_name == 'user_profile':
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"user_type": "System Administrator"})
            return mock_tbl
        elif table_name == 'organization':
            mock_tbl.select.return_value.order.return_value = mock_org_list
            return mock_tbl
        elif table_name == 'organization_internal':
            mock_tbl.select.return_value = mock_internal_list
            return mock_tbl
        return mock_tbl
        
    mock_client.table.side_effect = mock_table_routing
    
    response = client.get("/api/admin/organizations")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["organization_name"] == "Test Org"
    assert data[0]["overhead_grant"] == 0.1


@patch("project_funding_ledger.supabase_client.create_client")
def test_cancel_all_import_batch_success(mock_create_client, client):
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None
    mock_create_client.return_value = mock_client
    
    # Mock user_res returning admin
    mock_user_res = MagicMock()
    mock_user_res.user.id = "admin-id"
    mock_client.auth.get_user.return_value = mock_user_res
    
    # Mock profile response for role verification
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"id": "profile-id-123", "user_type": "System Administrator"})
    
    # Mock update execution
    mock_client.table.return_value.update.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(data=[])
    
    response = client.post("/admin/import/organizations/batches/batch-123/cancel-all")
    assert response.status_code == 200
    assert "cancelled successfully" in response.get_json()["message"]


@patch("openpyxl.load_workbook")
@patch("supabase.create_client")
def test_process_organization_import_slug_conflict(mock_create_client, mock_load_workbook):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    
    # Mock database to return:
    # 1. key check: returns empty (it is a Create)
    # 2. slug check: returns an existing organization record (conflict!)
    mock_key_check = MagicMock()
    mock_key_check.execute.side_effect = [
        MagicMock(data=[]), # key check
        MagicMock(data=[{"id": "conflicting-uuid", "organization_name": "Conflict Org"}]) # slug check (conflict)
    ]
    
    mock_tables = {}
    def mock_table_routing(table_name):
        if table_name not in mock_tables:
            mock_tables[table_name] = MagicMock()
        mock_tbl = mock_tables[table_name]
        if table_name == 'organization_key':
            mock_tbl.select.return_value.eq.return_value = mock_key_check
        elif table_name == 'organization':
            mock_tbl.select.return_value.eq.return_value = mock_key_check
        elif table_name == 'user_profile':
            mock_tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"id": "prof-1"})
        return mock_tbl
        
    mock_client.table.side_effect = mock_table_routing
    
    mock_wb = MagicMock()
    mock_sheet = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_wb.active = mock_sheet
    
    mock_row_data = [
        ("Organization_PFL_Key", "Organization Name", "Organziation Slug", "Description", "github page", "Project Website", "Donation Link", "Join Date", "Contacts", "Governing Agreements", "Reporting Obligations", "Documents", "Type", "Grant Overhead", "General Donation Overhead", "Corporate Donation Overhead", "Internal Notes"),
        ("ORG-NEW", "New Org Name", "conflict-slug", "", "", "", "", "", "", "", "", "", "Event", "10%", "15.0", 5, "")
    ]
    mock_sheet.iter_rows.return_value = mock_row_data
    
    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove:
        process_organization_import_task("dummy_path.xlsx", "batch-123")
        
        # Verify that the staging row was inserted with status "Error" and slug conflict message
        insert_mock = mock_tables['organization_import_row'].insert
        assert insert_mock.call_count == 1
        insert_calls = insert_mock.call_args_list
        assert insert_calls[0][0][0]["status"] == "Error"
        assert "Slug conflict" in insert_calls[0][0][0]["error_message"]




