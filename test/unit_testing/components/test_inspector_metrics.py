import os
import pytest
import pandas as pd
import ast
from components.inspector import Inspector

@pytest.fixture
def mock_inspector_dependencies(mocker):
    # Use mocker.patch to mock dependencies
    mock_open_file = mocker.patch(
        "builtins.open", new_callable=mocker.mock_open
    )
    mock_ast_parse = mocker.patch("ast.parse")
    MockLibraryExtractor = mocker.patch(
        "components.inspector.LibraryExtractor"
    )
    MockVariableExtractor = mocker.patch(
        "components.inspector.VariableExtractor"
    )
    MockDataFrameExtractor = mocker.patch(
        "components.inspector.DataFrameExtractor"
    )
    MockModelExtractor = mocker.patch("components.inspector.ModelExtractor")
    MockRuleChecker = mocker.patch("components.inspector.RuleChecker")

    yield {
        "mock_open": mock_open_file,
        "mock_ast_parse": mock_ast_parse,
        "MockLibraryExtractor": MockLibraryExtractor,
        "MockVariableExtractor": MockVariableExtractor,
        "MockDataFrameExtractor": MockDataFrameExtractor,
        "MockModelExtractor": MockModelExtractor,
        "MockRuleChecker": MockRuleChecker,
    }


def test_inspect_returns_metrics(mock_inspector_dependencies):
    # Unpack mocks
    mock_open_file = mock_inspector_dependencies["mock_open"]
    mock_ast_parse = mock_inspector_dependencies["mock_ast_parse"]
    MockLibraryExtractor = mock_inspector_dependencies["MockLibraryExtractor"]
    MockVariableExtractor = mock_inspector_dependencies["MockVariableExtractor"]
    MockDataFrameExtractor = mock_inspector_dependencies["MockDataFrameExtractor"]
    MockModelExtractor = mock_inspector_dependencies["MockModelExtractor"]
    MockRuleChecker = mock_inspector_dependencies["MockRuleChecker"]

    # Setup mock objects
    mock_rule_checker = MockRuleChecker.return_value
    mock_library_extractor = MockLibraryExtractor.return_value
    mock_variable_extractor = MockVariableExtractor.return_value
    mock_data_frame_extractor = MockDataFrameExtractor.return_value
    mock_model_extractor = MockModelExtractor.return_value

    # Configure mocks
    mock_library_extractor.get_library_aliases.return_value = {}
    mock_variable_extractor.extract_variable_definitions.return_value = []
    mock_data_frame_extractor.extract_dataframe_variables.return_value = []
    mock_model_extractor.model_dict = {}
    mock_model_extractor.tensor_operations_dict = {}
    mock_model_extractor.load_model_methods.return_value = {}

    # Mock RuleChecker to return an empty DataFrame (no smells)
    mock_rule_checker.rule_check.return_value = pd.DataFrame(
        columns=[
            "filename",
            "function_name",
            "smell_name",
            "line",
            "description",
            "additional_info",
        ]
    )

    # Mock file contents with 3 lines
    mock_file_contents = """import os
print("hello")
print("world")
"""
    mock_open_file.return_value.read.return_value = mock_file_contents

    # Mock AST to mimic empty module
    mock_ast_parse.return_value = ast.Module(body=[])

    # Instantiate the Inspector
    inspector = Inspector(output_path="mock_output_path")
    inspector.rule_checker = mock_rule_checker

    # Call inspect
    result = inspector.inspect("mock_file.py")

    # VERIFICATION
    # Check that result is a tuple
    assert isinstance(result, tuple), "Inspect should return a tuple"
    assert len(result) == 2, "Inspect should return (dataframe, loc)"
    
    df, loc = result
    
    # Check DataFrame
    assert isinstance(df, pd.DataFrame)
    
    # Check LOC
    assert isinstance(loc, int)
    assert loc == 3, "LOC should be 3 (based on mock_file_contents)"
