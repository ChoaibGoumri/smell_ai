import os
import pytest
import pandas as pd
import shutil
from components.project_analyzer import ProjectAnalyzer
from report.report_generator import ReportGenerator

@pytest.fixture
def density_integration_setup(tmp_path):
    # Setup directories
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create a python file to analyze
    # 5 lines of code
    code = """
import os
def foo():
    print('hello')
    return 1
"""
    (project_root / "test_file.py").write_text(code.strip())
    
    return str(project_root), str(output_dir)

def test_density_full_flow(density_integration_setup, mocker):
    input_path, output_path = density_integration_setup
    
    # 1. RUN ANALYZER
    # We need to mock RuleChecker to return smells for our file, 
    # but let ProjectAnalyzer and Inspector run normally to capture LOC.
    # Inspector uses RuleChecker.
    
    # Assuming RuleChecker relies on real classes unless mocked. 
    # To avoid relying on real smell detection (which might be empty for simple code),
    # let's mock RuleChecker.rule_check to return a fake smell.
    
    mock_rule_check = mocker.patch("components.rule_checker.RuleChecker.rule_check")
    mock_rule_check.return_value = pd.DataFrame([{
        "filename": os.path.join(input_path, "test_file.py"),
        "function_name": "foo",
        "smell_name": "FakeSmell",
        "line": 3,
        "description": "desc",
        "additional_info": "info"
    }])
    
    analyzer = ProjectAnalyzer(output_path)
    
    # analyze_project (single) output is incompatible with ReportGenerator (expects project_details folder).
    # So we use analyze_projects_sequential which handles structure correctly.
    # It expects a folder containing project folders. 
    # input_path is "test_project". Its parent is tmp_path.
    
    projects_root = os.path.dirname(input_path)
    analyzer.analyze_projects_sequential(projects_root)
    
    # VERIFY METRICS CSV CREATED
    # ProjectAnalyzer appends "output" to the base output path.
    # So it saves to output/output/project_details/projectname_metrics.csv
    
    actual_output_dir = os.path.join(output_path, "output")
    metrics_file = os.path.join(actual_output_dir, "project_details", "test_project_metrics.csv")
    assert os.path.exists(metrics_file), f"Metrics CSV not found at {metrics_file}"
    
    df_metrics = pd.read_csv(metrics_file)
    assert len(df_metrics) == 1
    assert "loc" in df_metrics.columns
    # Check LOC
    assert df_metrics["loc"].iloc[0] > 0
    
    # 2. RUN REPORT GENERATOR
    # ReportGenerator expects input_path to contain "project_details" folder.
    # actual_output_dir contains project_details.
    
    # ReportGenerator is interactive, we need to mock input to select '5' (Summary Report)
    mocker.patch("builtins.input", return_value="5")
    
    report_gen = ReportGenerator(input_path=actual_output_dir, output_path=output_path)
    report_gen.run()
    
    # VERIFY SUMMARY REPORT
    # Saved to output_path/summary_report.xlsx
    summary_file = os.path.join(output_path, "summary_report.xlsx")
    assert os.path.exists(summary_file), "Summary report Excel was not created"
    
    # Load Excel to verify columns
    # Pandas requires openpyxl
    try:
        # "test_project_Files"
        df_report = pd.read_excel(summary_file, sheet_name="test_project_Files")
        
        assert "loc" in df_report.columns
        assert "density" in df_report.columns
        assert "quality" in df_report.columns
        
        row = df_report.iloc[0]
        assert row["smells"] == 1 # From our mock
        assert row["loc"] > 0
        assert row["density"] > 0
        assert row["quality"] in ["Low", "Medium", "High"]
        
    except Exception as e:
        pytest.fail(f"Failed to read or verify Excel report: {e}")
