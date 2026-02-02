import os
import sys
import pandas as pd

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.inspector import Inspector

def run():
    inspector = Inspector(output_path="output_test_cr4")
    
    target_file = os.path.abspath("reproduce_issue_cr4.py")
    results = inspector.inspect(target_file)
    
    print("Detected Smells:")
    if not results.empty:
        print(results[["line", "smell_name", "additional_info"]].to_string(index=False))
    else:
        print("No smells detected.")

if __name__ == "__main__":
    run()
