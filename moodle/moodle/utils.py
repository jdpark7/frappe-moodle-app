import frappe
import requests
import string
import random

def get_moodle_settings():
    settings = frappe.get_doc("Moodle Settings")
    if not settings.moodle_url or not settings.api_token:
        frappe.throw("Please configure Moodle Settings first.")
    return settings.moodle_url, settings.api_token

def get_moodle_user_by_email(email):
    """
    Search for a Moodle user by email.
    Returns: dict with 'id', 'username', 'fullname' if found, else None
    """
    url, token = get_moodle_settings()
    
    endpoint = f"{url}/webservice/rest/server.php"
    params = {
        "wstoken": token,
        "wsfunction": "core_user_get_users",
        "moodlewsrestformat": "json",
        "criteria[0][key]": "email",
        "criteria[0][value]": email
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and (data.get('exception') or data.get('errorcode')):
             frappe.throw(f"Moodle API Error: {data.get('message')}")
        
        users = data.get('users', [])
        if users:
            return users[0] # Return the first matching user
        return None
        
    except Exception as e:
        frappe.log_error(f"Moodle User Lookup Failed: {e}")
        raise e

def get_courses_by_moodle_id(moodle_user_id):
    """
    Get courses for a specific Moodle User ID.
    """
    url, token = get_moodle_settings()
    
    endpoint = f"{url}/webservice/rest/server.php"
    params = {
        "wstoken": token,
        "wsfunction": "core_enrol_get_users_courses",
        "moodlewsrestformat": "json",
        "userid": moodle_user_id
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and (data.get('exception') or data.get('errorcode')):
             frappe.throw(f"Moodle API Error: {data.get('message')}")
        
        # Inject viewurl manually since it's missing from API response
        for course in data:
            if 'id' in course:
                course['viewurl'] = f"{url}/course/view.php?id={course['id']}"
             
        return data
        
    except Exception as e:
        frappe.log_error(f"Moodle Course Fetch Failed: {e}")
        raise e

def create_moodle_user(user_doc, password=None):
    """
    Create a new user in Moodle based on Frappe User Doc.
    """
    url, token = get_moodle_settings()
    endpoint = f"{url}/webservice/rest/server.php"
    
    # Generate a robust password if none provided
    if not password:
        length = 12
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password_chars = [
            random.choice(string.ascii_lowercase),
            random.choice(string.ascii_uppercase),
            random.choice(string.digits),
            random.choice("!@ #$%^&*") 
        ]
        password_chars += [random.choice(chars) for _ in range(length - 4)]
        random.shuffle(password_chars)
        password = "".join(password_chars)
    
    # Use email as username for consistency
    username = user_doc.email
    
    params = {
        "wstoken": token,
        "wsfunction": "core_user_create_users",
        "moodlewsrestformat": "json",
        "users[0][username]": username,
        "users[0][password]": password,
        "users[0][firstname]": user_doc.first_name,
        "users[0][lastname]": user_doc.last_name or ".",
        "users[0][email]": user_doc.email,
        "users[0][auth]": "manual",
    }
    
    try:
        response = requests.post(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and (data.get('exception') or data.get('errorcode')):
             frappe.throw(f"Moodle API Error: {data.get('message')}")
             
        # Success response is a list with the new user dict
        if data:
            user_data = data[0]
            user_data['generated_password'] = password
            return user_data
        return None
        
    except Exception as e:
        frappe.log_error(f"Moodle User Creation Failed: {e}")
        raise e
