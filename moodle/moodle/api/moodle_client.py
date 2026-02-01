import frappe
import requests
from urllib.parse import urljoin

class MoodleError(Exception):
    pass

def _get_settings():
    s = frappe.get_single("Moodle Settings")
    if not s.enabled:
        raise MoodleError("Moodle integration is disabled.")
    return s

def moodle_call(wsfunction: str, params: dict):
    s = _get_settings()
    base = s.moodle_base_url.rstrip("/") + "/"
    endpoint = s.rest_endpoint.lstrip("/")
    url = urljoin(base, endpoint)

    payload = {
        "wstoken": s.get_password("service_token"),
        "moodlewsrestformat": "json",
        "wsfunction": wsfunction,
        **params,
    }

    try:
        r = requests.post(url, data=payload, timeout=int(s.timeout_seconds))
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Moodle call failed")
        raise MoodleError(str(e))

    # Moodle WS standard error handling
    if isinstance(data, dict) and data.get("exception"):
        msg = data.get("message") or data.get("errorcode") or "Unknown Moodle WS error"
        frappe.log_error(f"{wsfunction} -> {data}", "Moodle WS exception")
        raise MoodleError(msg)

    return data

def get_or_create_moodle_userid(frappe_user_email: str) -> int:
    # 1) Check existing mapping in Frappe DB
    row = frappe.db.get_value(
        "Moodle User Map",
        {"moodle_email": frappe_user_email},
        ["name", "moodle_userid"],
        as_dict=True
    )
    if row and row.moodle_userid:
        return int(row.moodle_userid)

    # 2) Search user by email in Moodle
    data = moodle_call("core_user_get_users", {
        "criteria[0][key]": "email",
        "criteria[0][value]": frappe_user_email,
    })

    users = data.get("users") if isinstance(data, dict) else None
    if not users:
        raise MoodleError(f"Moodle user not found for email: {frappe_user_email}")

    moodle_userid = int(users[0]["id"])

    # 3) Save/Update mapping
    # Check if a map already exists for this frappe user to avoid duplicates if email changed
    existing_map = frappe.db.get_value("Moodle User Map", {"frappe_user": frappe.session.user}, "name")
    
    if existing_map:
        doc = frappe.get_doc("Moodle User Map", existing_map)
        doc.moodle_userid = moodle_userid
        doc.moodle_email = frappe_user_email
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc({
            "doctype": "Moodle User Map",
            "frappe_user": frappe.session.user, # Use current session user if email matches
            "moodle_userid": moodle_userid,
            "moodle_email": frappe_user_email,
        })
        doc.insert(ignore_permissions=True)
        
    return moodle_userid

def get_user_courses(moodle_userid: int):
    return moodle_call("core_enrol_get_users_courses", {"userid": moodle_userid})

def get_assignments_for_courses(course_ids: list[int]):
    # mod_assign_get_assignments often accepts courseids[0]=... format
    params = {}
    for i, cid in enumerate(course_ids):
        params[f"courseids[{i}]"] = int(cid)
    return moodle_call("mod_assign_get_assignments", params)
