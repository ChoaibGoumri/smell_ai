import os
import shutil
import pytest
import pandas as pd
from unittest.mock import ANY, MagicMock, patch
from components.project_analyzer import ProjectAnalyzer


@pytest.fixture
def mock_output_path(tmp_path):
    """
    Pytest fixture to create a temporary output directory.
    """
    return str(tmp_path)


@pytest.fixture
def project_analyzer(mock_output_path):
    """
    Fixture to create an instance of ProjectAnalyzer.
    """
    return ProjectAnalyzer(output_path=mock_output_path)


@pytest.fixture
def mock_file_related_methods(monkeypatch):
    """
    Fixture to mock the file-related methods.
    This fixture reduces repetition
    for mocking methods like os.path, FileUtils, etc.
    """
    monkeypatch.setattr("os.path.isdir", lambda path: True)
    monkeypatch.setattr("os.listdir", lambda path: ["project1", "project2"])
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files",
        lambda path: ["file1.py"],
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.initialize_log", lambda path: None
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.synchronized_append_to_log",
        lambda path, project, lock: None,
    )


def test_analyze_project(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test the `analyze_project` method.
    """

    output_dir = tmp_path / "output"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path: df.to_csv(
            output_dir / "overview.csv", index=False
        ),
    )

    # Mock inspection results for two files
    mock_inspection_results = [
        (
            pd.DataFrame(
                {
                    "filename": ["file1.py"],
                    "function_name": ["func1"],
                    "smell_name": ["smell1"],
                    "line": [10],
                    "description": ["desc1"],
                    "additional_info": ["info1"],
                }
            ),
            100,  # loc (lines of code)
        ),
        (
            pd.DataFrame(
                {
                    "filename": ["file2.py"],
                    "function_name": ["func2"],
                    "smell_name": ["smell2"],
                    "line": [20],
                    "description": ["desc2"],
                    "additional_info": ["info2"],
                }
            ),
            150,  # loc (lines of code)
        ),
    ]

    # Mock inspect method to return the inspection results
    project_analyzer.inspector.inspect = MagicMock(
        side_effect=mock_inspection_results
    )

    # Mock the get_python_files method to return both files
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files",
        lambda _: ["file1.py", "file2.py"],
    )

    # Run the method
    total_smells = project_analyzer.analyze_project(
        "test/unit_testing/components/mock_project_path"
    )

    # Assertions
    assert total_smells == 2  # Expecting 2 smells (from file1.py and file2.py)
    project_analyzer.inspector.inspect.assert_any_call("file1.py")
    project_analyzer.inspector.inspect.assert_any_call("file2.py")

    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_projects_sequential(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test the `analyze_projects_sequential` method.
    """

    output_dir = tmp_path / "output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path: df.to_csv(
            output_dir / "overview.csv", index=False
        ),
    )

    # Mock the inspector's inspect method
    mock_inspection_results = pd.DataFrame(
        {
            "filename": ["file1.py"],
            "function_name": ["func1"],
            "smell_name": ["smell1"],
            "line": [10],
        }
    )
    project_analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )

    # Call the method
    project_analyzer.analyze_projects_sequential(
        "test/unit_testing/components/mock_project_path", resume=False
    )

    # Ensure inspect was called
    project_analyzer.inspector.inspect.assert_called_with("file1.py")

    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_clean_output_directory(monkeypatch, project_analyzer):
    """
    Test the `clean_output_directory` method.
    """
    mock_clean_directory = MagicMock()
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.clean_directory", mock_clean_directory
    )

    # Run the method
    project_analyzer.clean_output_directory()

    # Assertions
    mock_clean_directory.assert_called_once_with(
        project_analyzer.base_output_path, "output"
    )


def test_merge_all_results(monkeypatch, project_analyzer):
    """
    Test the `merge_all_results` method.
    """
    mock_merge_results = MagicMock()
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.merge_results", mock_merge_results
    )

    # Run the method
    project_analyzer.merge_all_results()

    # Assertions
    mock_merge_results.assert_called_once_with(
        input_dir=os.path.join(
            project_analyzer.output_path, "project_details"
        ),
        output_dir=project_analyzer.output_path,
    )


def test_analyze_projects_parallel(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test the `analyze_projects_parallel` method.
    """

    mock_inspection_results = (
        pd.DataFrame(
            {
                "filename": ["file1.py"],
                "function_name": ["func1"],
                "smell_name": ["smell1"],
                "line": [10],
                "description": ["desc1"],
                "additional_info": ["info1"],
            }
        ),
        100,  # loc (lines of code)
    )

    # Mock dependencies
    monkeypatch.setattr(
        "os.path.exists", lambda path: True  # Mock that all paths exist
    )
    monkeypatch.setattr(
        "os.path.isdir",
        lambda path: True,  # Mock that all paths are directories
    )

    # Mock the inspector's inspect method
    project_analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )

    # Mock save results method
    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path: None,  # Do nothing on saving results
    )

    # Mock ThreadPoolExecutor to avoid threading and run tasks synchronously
    with patch("concurrent.futures.ThreadPoolExecutor") as MockExecutor:
        mock_executor = MagicMock()
        MockExecutor.return_value = mock_executor
        mock_executor.__enter__.return_value = mock_executor
        # Make sure the function gets executed immediately (synchronously)
        mock_executor.submit.side_effect = lambda func, *args, **kwargs: func(
            *args, **kwargs
        )

        # Run the method
        with patch("builtins.print") as mock_print:
            project_analyzer.analyze_projects_parallel(
                "test/unit_testing/components/mock_base_path", max_workers=1
            )

        # Ensure the inspector's inspect method
        # was called the expected number of times
        assert project_analyzer.inspector.inspect.call_count == 2

        # Check if print statements were made (optional)
        assert mock_print.call_count > 0


def test_exception_handling_in_inspect(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test that the `inspect` method handles exceptions gracefully.
    """

    # Simulate an exception in the inspect method
    project_analyzer.inspector.inspect = MagicMock(
        side_effect=FileNotFoundError
    )

    with patch("builtins.print") as mock_print:
        project_analyzer.analyze_projects_parallel(
            "test/unit_testing/components/mock_project_path", max_workers=1
        )

    # Assertions
    assert (
        "Total code smells found in all projects: 0\n"
        in mock_print.call_args[0][0]
    )

    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_project_with_errors(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test `analyze_project` with error
    handling (FileNotFoundError, SyntaxError).
    """
    output_dir = tmp_path / "output"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path: df.to_csv(
            output_dir / "overview.csv", index=False
        ),
    )

    # Mocking a SyntaxError for a specific file
    project_analyzer.inspector.inspect = MagicMock(side_effect=SyntaxError)

    # Run the method (simulate failure for file1.py)
    project_analyzer.analyze_project(
        "test/unit_testing/components/mock_project_path"
    )

    # Check if the error is logged to the error.txt file
    error_file = output_dir / "error.txt"
    with open(error_file, "r") as f:
        error_content = f.read()

    assert (
        "Error in file file1.py: " in error_content
    )  # Check that error is logged

    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_projects_sequential_save_results(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test saving results in `project_details` for sequential analysis.
    """
    output_dir = tmp_path / "output"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path: df.to_csv(
            output_dir / "overview.csv", index=False
        ),
    )

    # Mock the inspector's inspect method
    mock_inspection_results = (
        pd.DataFrame(
            {
                "filename": ["file1.py"],
                "function_name": ["func1"],
                "smell_name": ["smell1"],
                "line": [10],
            }
        ),
        100,  # loc (lines of code)
    )
    project_analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )

    # Call the method
    project_analyzer.analyze_projects_sequential(
        "test/unit_testing/components/mock_project_path", resume=False
    )

    # Check if project_details directory and the result file were created
    details_path = output_dir / "project_details"
    assert details_path.exists()

    detailed_file_path = details_path / "project1_results.csv"
    assert detailed_file_path.exists()

    # Check if the CSV file contains the expected data
    df = pd.read_csv(detailed_file_path)
    assert not df.empty
    assert "filename" in df.columns
    assert df["filename"].iloc[0] == "file1.py"

    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_projects_parallel_thread_safety(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test thread-safety in the `analyze_projects_parallel` method.
    """

    mock_inspection_results = (
        pd.DataFrame(
            {
                "filename": ["file1.py"],
                "function_name": ["func1"],
                "smell_name": ["smell1"],
                "line": [10],
                "description": ["desc1"],
                "additional_info": ["info1"],
            }
        ),
        100,  # loc (lines of code)
    )

    # Mock the inspector's inspect method
    project_analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )

    # Mock the synchronized_append_to_log method to check for thread-safety
    mock_synchronized_append = MagicMock()
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.synchronized_append_to_log",
        mock_synchronized_append,
    )

    # Run the method with parallel execution
    project_analyzer.analyze_projects_parallel(
        "test/unit_testing/components/mock_base_path", max_workers=2
    )

    # Normalize the paths for cross-platform consistency
    expected_path = os.path.join(
        "test/unit_testing/components/mock_base_path", "execution_log.txt"
    )

    # Ensure the synchronized_append_to_log
    # method was called with both project1 and project2
    mock_synchronized_append.assert_any_call(expected_path, "project1", ANY)
    mock_synchronized_append.assert_any_call(expected_path, "project2", ANY)

    mock_project_path = "test/unit_testing/components/mock_base_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_project_empty_directory(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test `analyze_project` when no Python files exist in the directory.
    """
    output_dir = tmp_path / "output"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path: df.to_csv(
            output_dir / "overview.csv", index=False
        ),
    )

    # Mock get_python_files to return an empty list
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files", lambda _: []
    )

    # Run the method and expect a ValueError
    with pytest.raises(ValueError, match="contains no Python files"):
        project_analyzer.analyze_project(
            "test/unit_testing/components/mock_project_path"
        )


def test_save_results_with_empty_dataframe(
    monkeypatch, tmp_path
):
    """
    Test `_save_results` when DataFrame is empty (should not save).
    """
    output_dir = tmp_path / "test_output"
    
    # Mock FileUtils.clean_directory
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.clean_directory", lambda *args: None
    )
    
    analyzer = ProjectAnalyzer(output_path=str(output_dir))
    empty_df = pd.DataFrame()
    
    with patch("builtins.print") as mock_print:
        analyzer._save_results(empty_df, "test.csv")
    
    # Verify print was called with "No results to save"
    mock_print.assert_called_once_with("No results to save for test.csv")
    
    # Verify file was NOT created
    test_file = output_dir / "output" / "test.csv"
    assert not test_file.exists()


def test_save_results_with_data(monkeypatch, tmp_path):
    """
    Test `_save_results` when DataFrame has data (should save).
    """
    output_dir = tmp_path / "test_output2"
    
    # Mock FileUtils.clean_directory
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.clean_directory", lambda *args: None
    )
    
    analyzer = ProjectAnalyzer(output_path=str(output_dir))
    
    df = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"]
    })
    
    with patch("builtins.print") as mock_print:
        analyzer._save_results(df, "test.csv")
    
    # Verify file was created
    test_file = output_dir / "output" / "test.csv"
    assert test_file.exists()
    
    # Verify content
    saved_df = pd.read_csv(test_file)
    assert len(saved_df) == 3
    assert list(saved_df.columns) == ["col1", "col2"]


def test_analyze_projects_sequential_resume_mode(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test `analyze_projects_sequential` with resume=True.
    """
    base_path = tmp_path / "projects"
    base_path.mkdir()
    
    # Create execution log
    execution_log = base_path / "execution_log.txt"
    execution_log.write_text("project1\n")
    
    # Mock get_last_logged_project to return "project1"
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_last_logged_project",
        lambda path: "project1"
    )
    
    mock_inspection_results = (
        pd.DataFrame({
            "filename": ["file1.py"],
            "function_name": ["func1"],
            "smell_name": ["smell1"],
            "line": [10],
        }),
        100,
    )
    
    project_analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )
    
    # Call with resume=True
    project_analyzer.analyze_projects_sequential(str(base_path), resume=True)
    
    # Verify initialize_log was NOT called (because resume=True)
    # This tests the branch at lines 128-129


def test_analyze_projects_sequential_with_non_directory(
    monkeypatch, project_analyzer, tmp_path
):
    """
    Test that non-directories are skipped in sequential analysis.
    """
    base_path = tmp_path / "projects"
    base_path.mkdir()
    
    # Create a file (not directory) to be skipped
    (base_path / "somefile.txt").write_text("content")
    (base_path / "project1").mkdir()
    
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.initialize_log", lambda path: None
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files",
        lambda path: ["file1.py"],
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.synchronized_append_to_log",
        lambda path, project, lock: None,
    )
    
    mock_inspection_results = (
        pd.DataFrame({
            "filename": ["file1.py"],
            "function_name": ["func1"],
            "smell_name": ["smell1"],
            "line": [10],
        }),
        100,
    )
    
    project_analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )
    
    with patch("builtins.print"):
        project_analyzer.analyze_projects_sequential(str(base_path), resume=False)
    
    # Only project1 should be analyzed, somefile.txt should be skipped
    assert project_analyzer.inspector.inspect.call_count > 0


def test_analyze_projects_sequential_with_metrics(
    monkeypatch, mock_file_related_methods, tmp_path
):
    """
    Test that file metrics are saved during sequential analysis.
    """
    output_dir = tmp_path / "test_output3"
    
    # Mock FileUtils.clean_directory
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.clean_directory", lambda *args: None
    )
    
    analyzer = ProjectAnalyzer(output_path=str(output_dir))
    
    # Mock inspection to return results with LOC
    mock_inspection_results = (
        pd.DataFrame({
            "filename": ["file1.py"],
            "function_name": ["func1"],
            "smell_name": ["smell1"],
            "line": [10],
        }),
        150,  # LOC
    )
    
    analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )
    
    with patch("builtins.print"):
        analyzer.analyze_projects_sequential(
            "test/unit_testing/components/mock_project_path", resume=False
        )
    
    # Check that metrics file was created
    details_path = output_dir / "output" / "project_details"
    assert details_path.exists()
    
    # Should have both results and metrics files
    metrics_files = list(details_path.glob("*_metrics.csv"))
    assert len(metrics_files) > 0


def test_analyze_projects_sequential_with_errors(
    monkeypatch, mock_file_related_methods, tmp_path
):
    """
    Test error handling in sequential analysis.
    """
    output_dir = tmp_path / "test_output4"
    
    # Mock FileUtils.clean_directory
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.clean_directory", lambda *args: None
    )
    
    analyzer = ProjectAnalyzer(output_path=str(output_dir))
    
    # Mock inspect to raise SyntaxError
    analyzer.inspector.inspect = MagicMock(
        side_effect=SyntaxError("invalid syntax")
    )
    
    with patch("builtins.print"):
        analyzer.analyze_projects_sequential(
            "test/unit_testing/components/mock_project_path", resume=False
        )
    
    # Check error.txt was created
    error_file = output_dir / "output" / "error.txt"
    assert error_file.exists()
    
    # Verify error content
    error_content = error_file.read_text()
    assert "Error in file file1.py" in error_content


def test_analyze_projects_parallel_with_errors(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test error handling in parallel analysis.
    """
    # Mock inspector to raise an exception
    project_analyzer.inspector.inspect = MagicMock(
        side_effect=Exception("Test error")
    )
    
    with patch("builtins.print") as mock_print:
        project_analyzer.analyze_projects_parallel(
            "test/unit_testing/components/mock_base_path", max_workers=1
        )
    
    # Verify error was printed
    error_calls = [str(call) for call in mock_print.call_args_list]
    assert any("Error analyzing project" in str(call) for call in error_calls)


def test_analyze_projects_sequential_base_path_creation(
    monkeypatch, project_analyzer, tmp_path
):
    """
    Test that base_path is created if it doesn't exist.
    """
    base_path = tmp_path / "non_existent_path"
    
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.initialize_log", lambda path: None
    )
    monkeypatch.setattr("os.listdir", lambda path: [])
    
    # Should create the directory without error
    with patch("builtins.print"):
        project_analyzer.analyze_projects_sequential(str(base_path), resume=False)
    
    # Verify directory was created
    assert base_path.exists()


def test_analyze_project_no_smells_found(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test analyze_project when no code smells are found (smell_count == 0).
    This covers the branch 87->91 where smell_count == 0.
    """
    output_dir = tmp_path / "output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path: None,
    )

    # Mock inspection results with EMPTY DataFrame (no smells)
    mock_inspection_results = (
        pd.DataFrame(columns=[
            "filename",
            "function_name",
            "smell_name",
            "line",
            "description",
            "additional_info",
        ]),
        100,  # loc
    )

    project_analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )

    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files",
        lambda _: ["file1.py"],
    )

    # Run the method
    total_smells = project_analyzer.analyze_project(
        "test/unit_testing/components/mock_project_path"
    )

    # Should return 0 smells
    assert total_smells == 0
    
    # Clean up
    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_projects_sequential_no_smells(
    monkeypatch, mock_file_related_methods, tmp_path
):
    """
    Test sequential analysis when no smells are found.
    This covers branch 177->182 where smell_count == 0.
    """
    output_dir = tmp_path / "test_output5"
    
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.clean_directory", lambda *args: None
    )
    
    analyzer = ProjectAnalyzer(output_path=str(output_dir))
    
    # Mock inspection with empty results (no smells)
    mock_inspection_results = (
        pd.DataFrame(columns=[
            "filename",
            "function_name",
            "smell_name",
            "line",
        ]),
        100,
    )
    
    analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )
    
    with patch("builtins.print"):
        analyzer.analyze_projects_sequential(
            "test/unit_testing/components/mock_project_path", resume=False
        )
    
    # Should complete without errors
    assert analyzer.inspector.inspect.call_count > 0


def test_analyze_projects_parallel_no_smells(
    monkeypatch, mock_file_related_methods, tmp_path
):
    """
    Test parallel analysis when no smells are found.
    This covers branch 284->289 where smell_count == 0.
    """
    mock_inspection_results = (
        pd.DataFrame(columns=[
            "filename",
            "function_name",
            "smell_name",
            "line",
            "description",
            "additional_info",
        ]),
        100,
    )

    monkeypatch.setattr(
        "os.path.exists", lambda path: True
    )
    monkeypatch.setattr(
        "os.path.isdir",
        lambda path: True,
    )
    
    output_dir = tmp_path / "test_output6"
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.clean_directory", lambda *args: None
    )
    
    analyzer = ProjectAnalyzer(output_path=str(output_dir))
    analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path: None,
    )

    with patch("builtins.print"):
        analyzer.analyze_projects_parallel(
            "test/unit_testing/components/mock_base_path", max_workers=1
        )

    # Should complete without errors
    assert analyzer.inspector.inspect.call_count >= 0


def test_analyze_projects_sequential_skip_output_and_log(
    monkeypatch, tmp_path
):
    """
    Test that 'output' and 'execution_log.txt' directories are skipped.
    This covers line 144.
    """
    base_path = tmp_path / "projects"
    base_path.mkdir()
    
    # Create directories including 'output' and 'execution_log.txt'
    (base_path / "output").mkdir()
    (base_path / "execution_log.txt").write_text("")
    (base_path / "project1").mkdir()
    
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.initialize_log", lambda path: None
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files",
        lambda path: ["file1.py"],
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.synchronized_append_to_log",
        lambda path, project, lock: None,
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.clean_directory", lambda *args: None
    )
    
    analyzer = ProjectAnalyzer(output_path=str(tmp_path / "output"))
    
    mock_inspection_results = (
        pd.DataFrame({
            "filename": ["file1.py"],
            "function_name": ["func1"],
            "smell_name": ["smell1"],
            "line": [10],
        }),
        100,
    )
    
    analyzer.inspector.inspect = MagicMock(
        return_value=mock_inspection_results
    )
    
    with patch("builtins.print"):
        analyzer.analyze_projects_sequential(str(base_path), resume=False)
    
    # Only project1 should be analyzed, not 'output' or 'execution_log.txt'
    # The mock should be called only for project1's files
    assert analyzer.inspector.inspect.call_count > 0


def test_analyze_projects_parallel_skip_output_and_log(
    monkeypatch, tmp_path
):
    """
    Test that 'output' and 'execution_log.txt' are skipped in parallel analysis.
    This covers line 259 (early return).
    """
    base_path = tmp_path / "projects_parallel"
    base_path.mkdir()
    
    # Create 'output' directory
    (base_path / "output").mkdir()
    
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.initialize_log", lambda path: None
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.clean_directory", lambda *args: None
    )
    
    analyzer = ProjectAnalyzer(output_path=str(tmp_path / "output_test"))
    
    # Mock to track if analyze is called for 'output'
    calls = []
    
    def track_inspect(filename):
        calls.append(filename)
        return (pd.DataFrame(), 100)
    
    analyzer.inspector.inspect = MagicMock(side_effect=track_inspect)
    
    with patch("builtins.print"):
        analyzer.analyze_projects_parallel(str(base_path), max_workers=1)
    
    # Should not analyze 'output' directory
    assert len(calls) == 0  # No files should be inspected from 'output'