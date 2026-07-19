import logging
import os
from project_funding_ledger.queue.registry import register_task

logger = logging.getLogger(__name__)

@register_task("placeholder_task")
def placeholder_task(x: int, y: int) -> int:
    """
    A placeholder background task that logs inputs and returns their sum.
    """
    logger.info(f"placeholder_task running with x={x}, y={y}")
    result = x + y
    logger.info(f"placeholder_task finished. Result={result}")
    return result

@register_task("log_audit_event")
def log_audit_event_task(audit_data: dict, access_token: str = None, refresh_token: str = None) -> dict:
    """
    Background task to write an audit log entry to the Supabase database.
    """
    logger.info(f"Executing log_audit_event background task for action={audit_data.get('action_type')}, entity={audit_data.get('entity_type')}")
    
    from supabase import create_client
    
    url = os.environ.get("SUPABASE_URL", "http://127.0.0.1:54321")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    
    # Initialize a clean client instance
    client = create_client(url, key)
    
    # If the user's session tokens are passed, authenticate the client context
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
            logger.info("Successfully restored user session context in background task.")
        except Exception as e:
            logger.warning(f"Failed to set user auth session in background task: {str(e)}")
            
    result = client.table('audit_log').insert(audit_data).execute()
    
    logger.info("Successfully wrote audit log to database.")
    return result.data if hasattr(result, 'data') else {}

@register_task("process_organization_import")
def process_organization_import_task(file_path: str, batch_id: str, access_token: str = None, refresh_token: str = None):
    """
    Background task to parse an uploaded Excel spreadsheet of organization data
    and stage each row in public.organization_import_row.
    """
    logger.info(f"Processing Excel organization import for batch_id={batch_id} from {file_path}")
    
    import openpyxl
    import datetime
    from supabase import create_client
    
    url = os.environ.get("SUPABASE_URL", "http://127.0.0.1:54321")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    client = create_client(url, key)
    
    profile_id = None
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
            user_res = client.auth.get_user()
            if user_res and user_res.user:
                profile_res = client.table('user_profile').select('id').eq('auth_user_id', user_res.user.id).single().execute()
                if profile_res.data:
                    profile_id = profile_res.data.get('id')
        except Exception as e:
            logger.warning(f"Failed to set session or query user profile: {str(e)}")
            
    # Try opening the workbook
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet = wb.active
    except Exception as e:
        logger.exception("Failed to open Excel workbook.")
        # If workbook loading failed, clean up the file and raise
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e

    # Helper parsers
    def clean_str(val):
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None

    def parse_date(val):
        if val is None:
            return None
        if isinstance(val, (datetime.date, datetime.datetime)):
            return val.date().isoformat()
        s = clean_str(val)
        if not s:
            return None
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y'):
            try:
                return datetime.datetime.strptime(s, fmt).date().isoformat()
            except ValueError:
                continue
        if isinstance(val, (int, float)):
            try:
                start = datetime.date(1899, 12, 30)
                return (start + datetime.timedelta(days=int(val))).isoformat()
            except Exception:
                pass
        raise ValueError(f"Invalid date format: {val}")

    def parse_numeric(val):
        if val is None:
            return 0.0
            
        has_percent = False
        if isinstance(val, str) and '%' in val:
            has_percent = True
            
        if isinstance(val, (int, float)):
            f_val = float(val)
        else:
            s = clean_str(val)
            if not s:
                return 0.0
            s = s.replace('%', '')
            try:
                f_val = float(s)
            except ValueError:
                raise ValueError(f"Invalid numeric format: {val}")
                
        if has_percent or f_val > 1.0:
            return f_val / 100.0
        return f_val
    
    # Identify header locations
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        logger.error("Excel sheet is empty.")
        if os.path.exists(file_path):
            os.remove(file_path)
        return
        
    header_row = rows[0]
    headers = [clean_str(h) for h in header_row]
    
    # Define mapping of columns to target keys
    col_mapping = {
        "Organization_PFL_Key": "import_key",
        "Organization Name": "organization_name",
        "Organziation Slug": "organization_slug",
        "Organization Slug": "organization_slug",  # fallback in case they fixed the typo
        "Description": "description",
        "github page": "source_code_url",
        "Project Website": "website_url",
        "Donation Link": "donation_url",
        "Join Date": "join_date",
        "Type": "organization_type",
        "Grant Overhead": "overhead_grant",
        "General Donation Overhead": "overhead_donation_general",
        "Corporate Donation Overhead": "overhead_donation_corporate",
        "Internal Notes": "notes"
    }
    
    header_indices = {}
    for i, h in enumerate(headers):
        if h in col_mapping:
            header_indices[col_mapping[h]] = i
            
    # Require at least the PFL key, name, and slug
    required_fields = ["import_key", "organization_name", "organization_slug"]
    for rf in required_fields:
        if rf not in header_indices:
            logger.error(f"Missing required header mapping for field: {rf}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return

    # Read data rows
    seen_slugs_in_batch = {}
    row_count = 0
    for r_idx, row in enumerate(rows):
        if r_idx == 0:

            continue  # Skip header
            
        row_count += 1
        
        # Get import key
        pfl_key_val = row[header_indices["import_key"]] if header_indices["import_key"] < len(row) else None
        import_key = clean_str(pfl_key_val)
        if not import_key:
            # Skip row if import key is empty
            continue
            
        try:
            # Extract fields using header indices
            raw_name = row[header_indices["organization_name"]] if header_indices["organization_name"] < len(row) else None
            raw_slug = row[header_indices["organization_slug"]] if header_indices["organization_slug"] < len(row) else None
            
            organization_name = clean_str(raw_name)
            organization_slug = clean_str(raw_slug)
            
            if not organization_name or not organization_slug:
                raise ValueError("Organization Name and Organization Slug cannot be empty.")
                
            # Check duplicate slug within the same batch
            if organization_slug in seen_slugs_in_batch:
                other_key = seen_slugs_in_batch[organization_slug]
                raise ValueError(f"Slug conflict: The slug '{organization_slug}' is duplicated within this spreadsheet (also used by key '{other_key}').")
            seen_slugs_in_batch[organization_slug] = import_key
                
            raw_desc = row[header_indices.get("description")] if "description" in header_indices and header_indices["description"] < len(row) else None
            raw_github = row[header_indices.get("source_code_url")] if "source_code_url" in header_indices and header_indices["source_code_url"] < len(row) else None
            raw_web = row[header_indices.get("website_url")] if "website_url" in header_indices and header_indices["website_url"] < len(row) else None
            raw_donation = row[header_indices.get("donation_url")] if "donation_url" in header_indices and header_indices["donation_url"] < len(row) else None
            raw_join = row[header_indices.get("join_date")] if "join_date" in header_indices and header_indices["join_date"] < len(row) else None
            raw_type = row[header_indices.get("organization_type")] if "organization_type" in header_indices and header_indices["organization_type"] < len(row) else None
            raw_grant_oh = row[header_indices.get("overhead_grant")] if "overhead_grant" in header_indices and header_indices["overhead_grant"] < len(row) else None
            raw_gen_oh = row[header_indices.get("overhead_donation_general")] if "overhead_donation_general" in header_indices and header_indices["overhead_donation_general"] < len(row) else None
            raw_corp_oh = row[header_indices.get("overhead_donation_corporate")] if "overhead_donation_corporate" in header_indices and header_indices["overhead_donation_corporate"] < len(row) else None
            raw_notes = row[header_indices.get("notes")] if "notes" in header_indices and header_indices["notes"] < len(row) else None

            # Parse fields
            description = clean_str(raw_desc)
            source_code_url = clean_str(raw_github)
            website_url = clean_str(raw_web)
            donation_url = clean_str(raw_donation)
            join_date = parse_date(raw_join)
            
            org_type = clean_str(raw_type)
            if org_type:
                if 'event' in org_type.lower():
                    organization_type = 'Event'
                else:
                    organization_type = 'Fiscal Sponsorship'
            else:
                organization_type = 'Fiscal Sponsorship'
                
            overhead_grant = parse_numeric(raw_grant_oh)
            overhead_donation_general = parse_numeric(raw_gen_oh)
            overhead_donation_corporate = parse_numeric(raw_corp_oh)
            notes = clean_str(raw_notes)
            
            proposed_data = {
                "organization_name": organization_name,
                "organization_slug": organization_slug,
                "description": description,
                "website_url": website_url,
                "source_code_url": source_code_url,
                "donation_url": donation_url,
                "join_date": join_date,
                "organization_type": organization_type,
                "status": "Active",
                "overhead_grant": overhead_grant,
                "overhead_donation_general": overhead_donation_general,
                "overhead_donation_corporate": overhead_donation_corporate,
                "notes": notes
            }
            
            # Check if this import key already exists in organization_key table
            key_res = client.table('organization_key').select('*').eq('import_key', import_key).execute()
            
            if not key_res.data:
                action_type = "Create"
                diff_data = None
                org_id = None
            else:
                action_type = "Update"
                org_id = key_res.data[0]['id']
                
            # Check if slug conflicts with an existing organization in the database
            slug_res = client.table('organization').select('id, organization_name').eq('organization_slug', organization_slug).execute()
            if slug_res.data:
                existing_org_id = slug_res.data[0]['id']
                existing_org_name = slug_res.data[0]['organization_name']
                if action_type == "Create" or (action_type == "Update" and org_id != existing_org_id):
                    raise ValueError(f"Slug conflict: The slug '{organization_slug}' is already in use by database organization '{existing_org_name}' (ID: {existing_org_id}).")
                
            if action_type == "Update":
                # Fetch existing organization details
                try:
                    org_res = client.table('organization').select('*').eq('id', org_id).single().execute()
                    existing_org = org_res.data or {}
                except Exception as e:
                    if 'PGRST116' in str(e) or '0 rows' in str(e) or 'Cannot coerce' in str(e):
                        raise ValueError(f"Organization metadata for key '{import_key}' (ID: {org_id}) was not found in the 'organization' table, though the mapping key exists.")
                    raise e
                    
                try:
                    org_internal_res = client.table('organization_internal').select('*').eq('id', org_id).single().execute()
                    existing_internal = org_internal_res.data or {}
                except Exception as e:
                    if 'PGRST116' in str(e) or '0 rows' in str(e) or 'Cannot coerce' in str(e):
                        raise ValueError(f"Internal details (overhead/notes) for key '{import_key}' (ID: {org_id}) were not found in the 'organization_internal' table, though the mapping key exists.")
                    raise e
                
                diff_data = {}
                def check_diff(field, old_v, new_v):
                    if old_v != new_v:
                        diff_data[field] = {"old": old_v, "new": new_v}

                check_diff("organization_name", existing_org.get("organization_name"), proposed_data["organization_name"])
                check_diff("organization_slug", existing_org.get("organization_slug"), proposed_data["organization_slug"])
                check_diff("description", existing_org.get("description"), proposed_data["description"])
                check_diff("website_url", existing_org.get("website_url"), proposed_data["website_url"])
                check_diff("source_code_url", existing_org.get("source_code_url"), proposed_data["source_code_url"])
                check_diff("donation_url", existing_org.get("donation_url"), proposed_data["donation_url"])
                check_diff("join_date", existing_org.get("join_date"), proposed_data["join_date"])
                check_diff("organization_type", existing_org.get("organization_type"), proposed_data["organization_type"])
                
                existing_grant_oh = float(existing_internal.get("overhead_grant") or 0.0)
                existing_gen_oh = float(existing_internal.get("overhead_donation_general") or 0.0)
                existing_corp_oh = float(existing_internal.get("overhead_donation_corporate") or 0.0)
                
                check_diff("overhead_grant", existing_grant_oh, proposed_data["overhead_grant"])
                check_diff("overhead_donation_general", existing_gen_oh, proposed_data["overhead_donation_general"])
                check_diff("overhead_donation_corporate", existing_corp_oh, proposed_data["overhead_donation_corporate"])
                check_diff("notes", existing_internal.get("notes"), proposed_data["notes"])
                
            # Stage the row in the staging table
            status = "Pending"
            resolved_at = None
            resolved_by_user_id = None
            
            if action_type == "Update" and not diff_data:
                status = "Confirmed"
                resolved_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                resolved_by_user_id = profile_id

            client.table('organization_import_row').insert({
                "batch_id": batch_id,
                "import_key": import_key,
                "action_type": action_type,
                "status": status,
                "organization_data": proposed_data,
                "diff_data": diff_data,
                "resolved_at": resolved_at,
                "resolved_by_user_id": resolved_by_user_id
            }).execute()
            
        except Exception as row_exc:
            logger.warning(f"Error parsing spreadsheet row {r_idx + 1}: {str(row_exc)}")
            err_msg = str(row_exc)
            if 'PGRST116' in err_msg or '0 rows' in err_msg or 'Cannot coerce' in err_msg:
                err_msg = f"Database query failed: Exactly one matching record was expected, but 0 were found in the database. This usually means a key mapping exists in organization_key but the organization or profile record is missing. Details: {err_msg}"
            try:
                client.table('organization_import_row').insert({
                    "batch_id": batch_id,
                    "import_key": import_key or "UNKNOWN",
                    "action_type": "Create",
                    "status": "Error",
                    "organization_data": {},
                    "error_message": err_msg
                }).execute()
            except Exception as db_exc:
                logger.error(f"Failed to record staging error in DB: {str(db_exc)}")

    logger.info(f"Finished staging {row_count} rows for batch_id={batch_id}")
    
    # Clean up temporary Excel file
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to remove temp file {file_path}: {str(e)}")


@register_task("confirm_organization_import_row")
def confirm_organization_import_row_task(row_id: str, access_token: str = None, refresh_token: str = None):
    """
    Background task to apply a single staging row to the main organization tables
    and mark the staging row status as Confirmed.
    """
    logger.info(f"Confirming organization import row id={row_id}")
    
    import datetime
    from supabase import create_client
    
    url = os.environ.get("SUPABASE_URL", "http://127.0.0.1:54321")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    client = create_client(url, key)
    
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception as e:
            logger.warning(f"Failed to set user auth session: {str(e)}")
            
    # Fetch staging row
    try:
        row_res = client.table('organization_import_row').select('*').eq('id', row_id).single().execute()
        if not row_res.data:
            raise ValueError(f"Staging row {row_id} not found.")
            
        row = row_res.data
        if row['status'] != 'Pending':
            raise ValueError(f"Staging row {row_id} has invalid status '{row['status']}', expected 'Pending'.")
            
        import_key = row['import_key']
        action_type = row['action_type']
        org_data = row['organization_data']
        
        profile_id = None
        try:
            user_res = client.auth.get_user()
            if user_res and user_res.user:
                profile_res = client.table('user_profile').select('id').eq('auth_user_id', user_res.user.id).single().execute()
                if profile_res.data:
                    profile_id = profile_res.data.get('id')
        except Exception:
            pass

        if action_type == "Create":
            # 1. Insert into organization_key
            key_res = client.table('organization_key').insert({
                "import_key": import_key,
                "created_by_user_id": profile_id,
                "updated_by_user_id": profile_id
            }).execute()
            
            if not key_res.data:
                raise ValueError("Failed to create organization_key record.")
                
            org_id = key_res.data[0]['id']
            
            # 2. Insert into organization
            client.table('organization').insert({
                "id": org_id,
                "organization_name": org_data["organization_name"],
                "organization_slug": org_data["organization_slug"],
                "status": org_data["status"],
                "organization_type": org_data["organization_type"],
                "description": org_data.get("description"),
                "website_url": org_data.get("website_url"),
                "source_code_url": org_data.get("source_code_url"),
                "donation_url": org_data.get("donation_url"),
                "join_date": org_data.get("join_date"),
                "created_by_user_id": profile_id,
                "updated_by_user_id": profile_id
            }).execute()
            
            # 3. Insert into organization_internal
            client.table('organization_internal').insert({
                "id": org_id,
                "overhead_grant": org_data.get("overhead_grant", 0.0),
                "overhead_donation_general": org_data.get("overhead_donation_general", 0.0),
                "overhead_donation_corporate": org_data.get("overhead_donation_corporate", 0.0),
                "notes": org_data.get("notes"),
                "created_by_user_id": profile_id,
                "updated_by_user_id": profile_id
            }).execute()
            
            logger.info(f"Successfully created organization '{org_data['organization_name']}' with ID {org_id}")
            
        elif action_type == "Update":
            # Find organization_key record
            key_res = client.table('organization_key').select('*').eq('import_key', import_key).execute()
            if not key_res.data:
                raise ValueError(f"Organization key mapping for import key '{import_key}' not found.")
                
            org_id = key_res.data[0]['id']
            
            # Update organization_key metadata
            client.table('organization_key').update({
                "updated_by_user_id": profile_id
            }).eq('id', org_id).execute()
            
            # Update organization
            client.table('organization').update({
                "organization_name": org_data["organization_name"],
                "organization_slug": org_data["organization_slug"],
                "status": org_data["status"],
                "organization_type": org_data["organization_type"],
                "description": org_data.get("description"),
                "website_url": org_data.get("website_url"),
                "source_code_url": org_data.get("source_code_url"),
                "donation_url": org_data.get("donation_url"),
                "join_date": org_data.get("join_date"),
                "updated_by_user_id": profile_id
            }).eq('id', org_id).execute()
            
            # Update organization_internal
            client.table('organization_internal').update({
                "overhead_grant": org_data.get("overhead_grant", 0.0),
                "overhead_donation_general": org_data.get("overhead_donation_general", 0.0),
                "overhead_donation_corporate": org_data.get("overhead_donation_corporate", 0.0),
                "notes": org_data.get("notes"),
                "updated_by_user_id": profile_id
            }).eq('id', org_id).execute()
            
            logger.info(f"Successfully updated organization '{org_data['organization_name']}' with ID {org_id}")
            
        # Mark row as Confirmed
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        client.table('organization_import_row').update({
            "status": "Confirmed",
            "resolved_by_user_id": profile_id,
            "resolved_at": now
        }).eq('id', row_id).execute()
        
    except Exception as e:
        logger.exception(f"Failed to confirm organization import row {row_id}")
        err_msg = str(e)
        if 'PGRST116' in err_msg or '0 rows' in err_msg or 'Cannot coerce' in err_msg:
            err_msg = f"Database query failed: Exactly one matching record was expected, but 0 were found in the database. This usually means a key mapping exists in organization_key but the organization or profile record is missing. Details: {err_msg}"
        try:
            client.table('organization_import_row').update({
                "status": "Error",
                "error_message": err_msg
            }).eq('id', row_id).execute()
        except Exception as db_exc:
            logger.error(f"Failed to record execution error for row {row_id}: {str(db_exc)}")
        raise e

