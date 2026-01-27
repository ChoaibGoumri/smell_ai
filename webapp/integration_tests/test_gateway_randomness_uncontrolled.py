import sys
import os
from fastapi.testclient import TestClient

# Adjust path to allow importing the static analysis app
# Assumes the test is run from project root or having root in pythonpath
# We need to ensure 'app' (inside staticanalysis) is resolvable or we import via full path
# The check_import.py showed we need 'webapp/services/staticanalysis' in path OR handle the 'from app...' imports
# If we run from root, 'webapp' is a package.
# But 'webapp.services.staticanalysis.app.main' does 'from app.routers...'
# meaningful that 'app' must be a top level package OR we are inside that dir.
# Let's try inserting the specific path.

current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, "webapp", "services", "staticanalysis"))

from webapp.services.staticanalysis.app.main import app

client = TestClient(app)

def test_randomness_uncontrolled_detected():
    code_snippet = """
from sklearn.ensemble import RandomForestClassifier

def train_model():
    rf = RandomForestClassifier()
    return rf
"""
    test_payload = {
        "code_snippet": code_snippet
    }

    # The endpoint is mapped at /detect_smell_static in the service router
    # AND included in the app.
    # checking the router: @router.post("/detect_smell_static", ...)
    
    response = client.post("/detect_smell_static", json=test_payload)
    
    # Debug print
    if response.status_code != 200:
        print(f"Error response: {response.text}")

    assert response.status_code == 200
    json_response = response.json()
    
    # Check if we got smells back
    # The response model is DetectSmellStaticResponse(success=..., smells=...)
    # smells can be list or string
    
    assert json_response["success"] is True
    smells = json_response["smells"]
    
    # We expect at least one smell, matching checking Randomness Uncontrolled
    randomness_smell = None
    if isinstance(smells, list):
        for smell in smells:
            if smell["smell_name"] == "Randomness Uncontrolled":
                randomness_smell = smell
                break
            
    assert randomness_smell is not None, f"Randomness Uncontrolled smell not found in response: {smells}"
    assert randomness_smell["function_name"] == "train_model"
    # Line 5: rf = RandomForestClassifier()
    assert randomness_smell["line"] == 5
    assert "RandomForestClassifier" in randomness_smell["additional_info"]

def test_randomness_controlled_no_smell():
    code_snippet = """
from sklearn.ensemble import RandomForestClassifier

def train_model():
    rf = RandomForestClassifier(random_state=42)
    return rf
"""
    test_payload = {
        "code_snippet": code_snippet
    }

    response = client.post("/detect_smell_static", json=test_payload)
    
    assert response.status_code == 200
    json_response = response.json()
    
    smells = json_response["smells"]
    
    if isinstance(smells, list):
        smell_names = [s["smell_name"] for s in smells]
        assert "Randomness Uncontrolled" not in smell_names
