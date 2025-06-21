#!/usr/bin/env python3
"""
Test script for the new assignment endpoints
This script tests the CRUD operations for assignments
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")

def test_assignment_endpoints():
    """Test the assignment CRUD endpoints"""
    
    print("🧪 Testing Assignment Endpoints")
    print("=" * 50)
    
    # Test data
    test_class_data = {
        "name": "Test Class for Assignment Management",
        "code": "TEST101",
        "description": "A test class for testing assignment endpoints"
    }
    
    test_assignment_data = {
        "name": "Test Assignment",
        "description": "This is a test assignment for testing the endpoints"
    }
    
    # Step 1: Create a test user (professor)
    print("1. Creating test professor user...")
    professor_data = {
        "email": "test_professor@test.com",
        "name": "Test Professor",
        "user_id": "test_prof_001",
        "password": "testpassword123",
        "is_professor": True
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/signup", json=professor_data)
        if response.status_code == 201:
            print("✅ Professor user created successfully")
        elif response.status_code == 400 and "already registered" in response.text:
            print("ℹ️ Professor user already exists")
        else:
            print(f"❌ Failed to create professor: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating professor: {e}")
        return
    
    # Step 2: Login as professor
    print("2. Logging in as professor...")
    login_data = {
        "username": professor_data["email"],
        "password": professor_data["password"]
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return
    
    # Step 3: Create a test class
    print("3. Creating test class...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{API_URL}/classes/", json=test_class_data, headers=headers)
        if response.status_code == 201:
            class_data = response.json()
            class_id = class_data["id"]
            print(f"✅ Test class created with ID: {class_id}")
        else:
            print(f"❌ Failed to create class: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating class: {e}")
        return
    
    # Step 4: Create a test assignment
    print("4. Creating test assignment...")
    assignment_create_data = {
        **test_assignment_data,
        "class_id": class_id
    }
    
    try:
        response = requests.post(f"{API_URL}/classes/{class_id}/assignments/", 
                               json=assignment_create_data, headers=headers)
        if response.status_code == 201:
            assignment_data = response.json()
            assignment_id = assignment_data["id"]
            print(f"✅ Test assignment created with ID: {assignment_id}")
        else:
            print(f"❌ Failed to create assignment: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating assignment: {e}")
        return
    
    # Step 5: Get the assignment
    print("5. Getting assignment details...")
    try:
        response = requests.get(f"{API_URL}/assignments/{assignment_id}", headers=headers)
        if response.status_code == 200:
            assignment = response.json()
            print(f"✅ Retrieved assignment: {assignment['name']}")
        else:
            print(f"❌ Failed to get assignment: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error getting assignment: {e}")
        return
    
    # Step 6: Update the assignment
    print("6. Updating assignment...")
    update_data = {
        "name": "Updated Test Assignment",
        "description": "This assignment has been updated for testing"
    }
    
    try:
        response = requests.put(f"{API_URL}/assignments/{assignment_id}", 
                              json=update_data, headers=headers)
        if response.status_code == 200:
            updated_assignment = response.json()
            print(f"✅ Assignment updated: {updated_assignment['name']}")
        else:
            print(f"❌ Failed to update assignment: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error updating assignment: {e}")
        return
    
    # Step 7: Get all assignments for the class
    print("7. Getting all assignments for the class...")
    try:
        response = requests.get(f"{API_URL}/classes/{class_id}/assignments/", headers=headers)
        if response.status_code == 200:
            assignments = response.json()
            print(f"✅ Found {len(assignments)} assignment(s) in the class")
        else:
            print(f"❌ Failed to get assignments: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error getting assignments: {e}")
        return
    
    # Step 8: Delete the assignment
    print("8. Deleting assignment...")
    try:
        response = requests.delete(f"{API_URL}/assignments/{assignment_id}", headers=headers)
        if response.status_code == 200:
            print("✅ Assignment deleted successfully")
        else:
            print(f"❌ Failed to delete assignment: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error deleting assignment: {e}")
        return
    
    # Step 9: Verify assignment is deleted
    print("9. Verifying assignment is deleted...")
    try:
        response = requests.get(f"{API_URL}/assignments/{assignment_id}", headers=headers)
        if response.status_code == 404:
            print("✅ Assignment successfully deleted (404 returned)")
        else:
            print(f"❌ Assignment still exists: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error verifying deletion: {e}")
        return
    
    print("\n🎉 All assignment endpoint tests passed!")
    print("=" * 50)

if __name__ == "__main__":
    test_assignment_endpoints() 