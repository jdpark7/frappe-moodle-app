import frappe
from frappe import _
from datetime import datetime, timezone
from moodle.moodle.api.moodle_client import (
    get_or_create_moodle_userid,
    get_user_courses,
    get_assignments_for_courses,
    MoodleError
)

def _cache_key(moodle_userid: int) -> str:
    return f"moodle_dashboard:{moodle_userid}"

@frappe.whitelist()
def dashboard(refresh: int = 0):
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw(_("Login required"), frappe.PermissionError)

    user = frappe.get_doc("User", frappe.session.user)
    email = user.email

    try:
        moodle_userid = get_or_create_moodle_userid(email)
    except MoodleError as e:
         frappe.throw(_("Failed to link Moodle user: {0}").format(str(e)))

    key = _cache_key(moodle_userid)
    ttl = int(frappe.get_single("Moodle Settings").cache_ttl_seconds or 600)

    if not int(refresh):
        cached = frappe.cache().get_value(key)
        if cached:
            cached["cached"] = True
            return cached

    try:
        courses = get_user_courses(moodle_userid) or []
        course_ids = [c["id"] for c in courses if "id" in c]

        # Assignments (for multiple courses at once)
        assigns_raw = get_assignments_for_courses(course_ids) if course_ids else {}
        due_assignments = _extract_due_assignments(assigns_raw)

        # Announcements: Recommended "Additional Implementation"
        # For now, return empty list or implement logic to fetch from specific forum
        announcements = []

        result = {
            "user": {"email": email, "moodle_userid": moodle_userid},
            "courses": _simplify_courses(courses),
            "announcements": announcements,
            "due_assignments": due_assignments,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "cached": False
        }
        frappe.cache().set_value(key, result, expires_in_sec=ttl)
        return result

    except MoodleError as e:
        # If failure, return stale cache if exists
        cached = frappe.cache().get_value(key)
        if cached:
            cached["cached"] = True
            cached["stale"] = True
            cached["error"] = str(e)
            return cached
        frappe.throw(str(e))

def _simplify_courses(courses: list[dict]):
    out = []
    for c in courses:
        out.append({
            "id": c.get("id"),
            "shortname": c.get("shortname"),
            "fullname": c.get("fullname"),
            "summary": c.get("summary"),
            "startdate": c.get("startdate"),
            "enddate": c.get("enddate"),
            "progress": c.get("progress"),
            "viewurl": c.get("viewurl")
        })
    return out

def _extract_due_assignments(assigns_raw: dict, limit: int = 10):
    # mod_assign_get_assignments response structure includes courses
    now = datetime.now(timezone.utc).timestamp()
    due = []

    courses = assigns_raw.get("courses", []) if isinstance(assigns_raw, dict) else []
    for c in courses:
        cid = c.get("id")
        for a in c.get("assignments", []) or []:
            duedate = a.get("duedate")  # unix timestamp
            if duedate and duedate >= now:
                due.append({
                    "course_id": cid,
                    "id": a.get("id"),
                    "name": a.get("name"),
                    "duedate": duedate,
                    "allowsubmissionsfromdate": a.get("allowsubmissionsfromdate"),
                    "cutoffdate": a.get("cutoffdate"),
                    "intro": a.get("intro")
                })

    due.sort(key=lambda x: x["duedate"])
    return due[:limit]
