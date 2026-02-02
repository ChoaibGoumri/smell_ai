import os
import pytest
import pandas as pd
from components.inspector import Inspector


# Helper to find dictionary paths regardless of where pytest is run from
def get_dictionary_paths():
    # Helper to resolve paths relative to this test file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up from test/unit_testing/components to smell_ai root
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))

    return {
        "dataframe_dict_path": os.path.join(project_root, "obj_dictionaries", "dataframes.csv"),
        "model_dict_path": os.path.join(project_root, "obj_dictionaries", "models.csv"),
        "tensor_dict_path": os.path.join(project_root, "obj_dictionaries", "tensors.csv"),
    }

DICT_PATHS = get_dictionary_paths()


def test_inspect_with_real_file(tmp_path):
    """Test inspect method with a real temporary file."""
    # Create a temporary Python file
    test_file = tmp_path / "test_code.py"
    test_code = """import pandas as pd

def my_function():
    df = pd.DataFrame()
    return df
"""
    test_file.write_text(test_code)
    
    # Create Inspector instance
    inspector = Inspector(output_path=str(tmp_path), **DICT_PATHS)
    
    # Call inspect
    result_df, loc = inspector.inspect(str(test_file))
    
    # Assertions
    assert isinstance(result_df, pd.DataFrame)
    assert isinstance(loc, int)
    assert loc == 5  # Number of lines
    
    expected_columns = [
        "filename",
        "function_name",
        "smell_name",
        "line",
        "description",
        "additional_info",
    ]
    assert list(result_df.columns) == expected_columns


def test_inspect_returns_tuple(tmp_path):
    """Test that inspect returns a tuple of (DataFrame, int)."""
    test_file = tmp_path / "simple.py"
    test_file.write_text("x = 1\n")
    
    inspector = Inspector(output_path=str(tmp_path), **DICT_PATHS)
    result = inspector.inspect(str(test_file))
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], pd.DataFrame)
    assert isinstance(result[1], int)


def test_inspect_file_not_found(tmp_path):
    """Test that FileNotFoundError is raised for non-existent file."""
    inspector = Inspector(output_path=str(tmp_path), **DICT_PATHS)
    
    with pytest.raises(FileNotFoundError, match="Error in file"):
        inspector.inspect("non_existent_file.py")


def test_inspect_syntax_error(tmp_path):
    """Test that SyntaxError is raised for file with syntax errors."""
    test_file = tmp_path / "syntax_error.py"
    test_file.write_text("def broken(\n")  # Incomplete function definition
    
    inspector = Inspector(output_path=str(tmp_path), **DICT_PATHS)
    
    with pytest.raises(SyntaxError, match="Error in file"):
        inspector.inspect(str(test_file))


def test_inspect_general_exception(tmp_path, mocker):
    """Test that general exceptions are raised and printed."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass\n")
    
    inspector = Inspector(output_path=str(tmp_path), **DICT_PATHS)
    
    # Mock rule_checker to raise an exception
    mock_rule_checker = mocker.Mock()
    mock_rule_checker.rule_check.side_effect = RuntimeError("Test error")
    inspector.rule_checker = mock_rule_checker
    
    with pytest.raises(RuntimeError, match="Test error"):
        with mocker.patch("builtins.print") as mock_print:
            inspector.inspect(str(test_file))
        
        # Verify error was printed
        assert any("Error processing function" in str(call) for call in mock_print.call_args_list)
