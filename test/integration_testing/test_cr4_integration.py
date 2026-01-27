import os
import pytest
import pandas as pd
from components.inspector import Inspector

@pytest.fixture
def cr4_file_setup(tmp_path):
    """
    Creates a temporary Python file with code that triggers the CR4 smell.
    """
    input_file = tmp_path / "test_cr4_code.py"
    input_file.write_text(
        """
import sklearn.ensemble as se
from sklearn.cluster import KMeans

def train_model():
    # SMELL: Missing n_estimators for RandomForestClassifier
    clf_bad = se.RandomForestClassifier()

    # NO SMELL: n_estimators is present
    clf_good = se.RandomForestClassifier(n_estimators=100)

    # SMELL: Missing n_clusters for KMeans
    km_bad = KMeans(random_state=42)

    # NO SMELL: n_clusters is present
    km_good = KMeans(n_clusters=3)
        """
    )
    return str(input_file)

def test_cr4_integration(cr4_file_setup):
    """
    Integration test for CR4: Hyperparameter not explicitly set.
    Uses the real Inspector and dictionary files to verify detection.
    """
    # Assuming testing is run from project root, where obj_dictionaries is located.
    # We verify paths exist first.
    cwd = os.getcwd()
    models_path = os.path.join(cwd, "obj_dictionaries", "models.csv")
    
    assert os.path.exists(models_path), f"Models dictionary not found at {models_path}"

    # Initialize Inspector with real paths (defaults should work if running from root)
    inspector = Inspector(output_path="test_output_cr4")
    
    # Run inspection
    result_df = inspector.inspect(cr4_file_setup)
    
    # Assertions
    assert not result_df.empty, "Inspector returned empty results"
    
    # Filter for our specific smell
    cr4_smells = result_df[result_df["smell_name"] == "hyperparameters_not_explicitly_set"]
    
    assert len(cr4_smells) == 2, f"Expected 2 CR4 smells, found {len(cr4_smells)}"
    
    # Check details of the first smell (RandomForestClassifier)
    # The line numbers should technically be 7 and 13 based on the string above (start counting lines)
    
    # Helper to check if a specific message is in additional_info for a given line
    def has_smell(lines, model_name, missing_param):
        for _, row in cr4_smells.iterrows():
            if (row["line"] in lines 
                and model_name in row["additional_info"] 
                and f"Missing critical configurations: {missing_param}" in row["additional_info"]):
                return True
        return False

    # SMELL 1: RandomForestClassifier (Line 7)
    assert has_smell([7], "RandomForestClassifier", "n_estimators"), \
        "Failed to detect missing n_estimators for RandomForestClassifier"

    # SMELL 2: KMeans (Line 13)
    assert has_smell([13], "KMeans", "n_clusters"), \
        "Failed to detect missing n_clusters for KMeans"
        
    print("Integration Test for CR4 Passed!")
