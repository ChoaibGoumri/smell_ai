import sys
import os
import pandas as pd

# Add current directory to path so we can import components
sys.path.append(os.getcwd())

from components.inspector import Inspector

def test_inspector():
    print("Testing Inspector...")
    inspector = Inspector(output_path="output_test")
    
    # Create a dummy python file
    with open("temp_test.py", "w") as f:
        f.write("import os\nprint('hello')\n")
    
    try:
        result = inspector.inspect("temp_test.py")
        print(f"Result type: {type(result)}")
        
        if isinstance(result, tuple):
            print(f"Result length: {len(result)}")
            df, loc = result
            print(f"DataFrame empty: {df.empty}")
            print(f"LOC: {loc}")
            print(f"LOC type: {type(loc)}")
        else:
            print("Result is NOT a tuple!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists("temp_test.py"):
            os.remove("temp_test.py")

if __name__ == "__main__":
    test_inspector()
