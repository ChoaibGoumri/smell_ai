import requests
import json

def test_service():
    url = "http://localhost:8002/detect_smell_static"
    payload = {
        "code_snippet": "import os\nprint('hello world')"
    }
    
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_service()
