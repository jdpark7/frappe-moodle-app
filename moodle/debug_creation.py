import frappe
from moodle.moodle.utils import get_moodle_settings, create_moodle_user
import requests
import json

def run():
    print("Debugging Moodle User Creation...")
    
    # 1. Check Settings
    url, token = get_moodle_settings()
    print(f"URL: {url}")
    print(f"Token: {token[:5]}...")
    
    # 2. Mock a generic user doc
    user_doc = frappe._dict({
        "email": "debug_test_user@example.com",
        "first_name": "Debug",
        "last_name": "User"
    })
    
    print("\nAttempting to create user: debug_test_user@example.com")
    
    try:
        # Call the logic directly
        # Note: We duplicate logic slightly to print raw response if utils throws too early
        endpoint = f"{url}/webservice/rest/server.php"
        
        # Make a simple password that definitely passes standard policies
        password = "DebugUser123!@#"
        
        params = {
            "wstoken": token,
            "wsfunction": "core_user_create_users",
            "moodlewsrestformat": "json",
            "users[0][username]": user_doc.email,
            "users[0][password]": password,
            "users[0][firstname]": user_doc.first_name,
            "users[0][lastname]": user_doc.last_name,
            "users[0][email]": user_doc.email,
            "users[0][auth]": "manual",
        }
        
        print("Sending Request...")
        response = requests.post(endpoint, params=params)
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print("\n--- RAW RESPONSE ---")
            print(json.dumps(data, indent=2))
        except:
            print(f"Raw Text: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
