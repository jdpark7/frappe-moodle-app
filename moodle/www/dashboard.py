import frappe
import frappe
from moodle.moodle.utils import get_moodle_user_by_email, get_courses_by_moodle_id, get_moodle_settings

def get_context(context):
    try:
        # 1. Identify current user's email
        current_user = frappe.session.user
        if current_user == "Guest":
            context.error = "Please log in to view your courses."
            return context
            
        # Fetch the actual user object to get the email
        user_doc = frappe.get_doc("User", current_user)
        user_email = user_doc.email
        
        context.user_email = user_email
        
        # Get Moodle URL for links
        moodle_url, _ = get_moodle_settings()
        context.moodle_url = moodle_url
        
        # 2. Look up Moodle User
        moodle_user = get_moodle_user_by_email(user_email)
        
        if moodle_user:
            context.found_moodle_user = moodle_user
            context.moodle_user_id = moodle_user.get('id')
            
            # 3. Fetch courses
            context.courses = get_courses_by_moodle_id(context.moodle_user_id)
        else:
            context.found_moodle_user = None
            context.account_warning = f"No Moodle account found for email: {user_email}"

    except Exception as e:
        context.error = str(e)
        
    return context

@frappe.whitelist()
def create_account(password=None):
    """
    Called by the dashboard button to create a Moodle account.
    """
    try:
        current_user = frappe.session.user
        if current_user == "Guest":
            frappe.throw("Please log in first.")
            
        user_doc = frappe.get_doc("User", current_user)
        
        # Call the utils function
        from moodle.moodle.utils import create_moodle_user
        new_user = create_moodle_user(user_doc, password=password)
        
        if new_user:
            return {"success": True, "message": f"Created Moodle account for {user_doc.email}", "user": new_user}
        else:
            return {"success": False, "message": "Failed to create user (No response data)."}
            
    except Exception as e:
        frappe.log_error(f"Create Account Failed: {e}")
        return {"success": False, "message": str(e)}
