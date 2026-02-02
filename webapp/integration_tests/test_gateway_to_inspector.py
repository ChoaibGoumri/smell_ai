from fastapi.testclient import TestClient
from webapp.gateway import main
# flake8: noqa

# Create the test client
client = TestClient(main.app)


from unittest.mock import patch, AsyncMock, MagicMock

# Test case to check gateway to static analysis service
@patch("webapp.gateway.main.httpx.AsyncClient")
def test_gateway_to_static_analysis_no_smell(mock_client):
    payload = {"code_snippet": "def my_function(): pass"}

    expected_response = {
        "smells": 'Static analysis returned no data'
    }

    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response

    mock_post = AsyncMock()
    mock_post.return_value = mock_response

    mock_instance = mock_client.return_value
    mock_instance.__aenter__.return_value.post = mock_post

    response = client.post(
        "/api/detect_smell_static", json=payload
    )

    assert response.status_code == 200
    assert response.json() == expected_response



# Test case to check gateway to static analysis service
@patch("webapp.gateway.main.httpx.AsyncClient")
def test_gateway_to_static_analysis_with_smell(mock_client):
    code_snippet = """
import json
import pandas as pd

def save_as_csv(
    self, train_data, val_data, train_file="train.csv", val_file="val.csv"
):
    pd.DataFrame(train_data).to_csv(train_file, index=False)
    pd.DataFrame(val_data).to_csv(val_file, index=False)
"""

    test_payload = {
        "code_snippet": code_snippet
    }

    # Mocked dataset input for testing
    expected_response = {
        "smells": [
            {
                "function_name": "save_as_csv",
                "line": 8,
                "smell_name": "columns_and_datatype_not_explicitly_set",
                "description": "Pandas' DataFrame or read_csv methods should explicitlyset 'dtype' to avoid unexpected behavior.",
                "additional_info": "Missing explicit 'dtype'in DataFrame call.",
            },
            {
                "function_name": "save_as_csv",
                "line": 9,
                "smell_name": "columns_and_datatype_not_explicitly_set",
                "description": "Pandas' DataFrame or read_csv methods should explicitlyset 'dtype' to avoid unexpected behavior.",
                "additional_info": "Missing explicit 'dtype'in DataFrame call.",
            },
        ]
    }

    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response

    mock_post = AsyncMock()
    mock_post.return_value = mock_response

    mock_instance = mock_client.return_value
    mock_instance.__aenter__.return_value.post = mock_post

    response = client.post("/api/detect_smell_static", json=test_payload)
    print(f"Response json: ", response.json())
    assert response.status_code == 200
    assert response.json() == expected_response

