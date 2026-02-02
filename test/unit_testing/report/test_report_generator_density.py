import io
import os
import pytest
import pandas as pd
from report.report_generator import ReportGenerator

@pytest.fixture
def mock_smell_data():
    return pd.DataFrame({
        "filename": ["file1.py", "file1.py", "file2.py"],
        "project_name": ["proj1", "proj1", "proj1"],
        "smell_name": ["Smell1", "Smell2", "Smell3"],
        "loc": [1000, 1000, 20] # file1: 2 smells / 1000 loc = 0.002 (Low), file2: 1 smell / 20 loc = 0.05 (High boundary)
    })

@pytest.fixture
def generator():
    return ReportGenerator(
        input_path="test_in",
        output_path="test_out"
    )

def test_summary_report_density_calculation(generator, mock_smell_data, mocker):
    # Mock ExcelWriter to capture the dataframe being written
    mock_excel_writer = mocker.patch("pandas.ExcelWriter", autospec=True)
    mock_file = io.BytesIO()
    mock_excel_writer.return_value.__enter__.return_value = mock_file
    
    # We need to intercept the to_excel calls to check the content
    # Using autospec=True ensures self is passed as the first argument
    mock_to_excel = mocker.patch("pandas.DataFrame.to_excel", autospec=True)
    
    generator.summary_report(mock_smell_data)
    
    # Analyze calls to to_excel
    # Expectation: 
    # 1. Project Summary sheet
    # 2. Files sheet (proj1_Files)
    
    # Find the call for the files sheet
    found_files_sheet = False
    
    for call in mock_to_excel.call_args_list:
        args, kwargs = call
        sheet_name = kwargs.get("sheet_name")
        
        # When autospec=True, args[0] is the dataframe!
        if len(args) > 0:
            df_written = args[0]
        else:
            continue
        
        if sheet_name and "Files" in sheet_name:
            found_files_sheet = True
            
            # Verify columns
            assert "density" in args[0].columns
            assert "quality" in args[0].columns
            
            # Verify content
            # file1.py: 2 smells, 1000 LOC. Density = 0.002. Quality < 0.005 -> "Low"
            file1_row = args[0][args[0]["filename"] == "file1.py"].iloc[0]
            assert file1_row["smells"] == 2
            assert file1_row["loc"] == 1000
            assert file1_row["density"] == 0.002
            assert file1_row["quality"] == "Low"
            
            # file2.py: 1 smell, 20 LOC. Density = 0.05. Quality >= 0.05 -> "High" (Actually >= 0.05 is High in my logic? let's check source)
            # Source: if d < 0.005: Low; elif d < 0.05: Medium; else: High.
            # 0.05 is NOT < 0.05, so it goes to else -> High.
            file2_row = args[0][args[0]["filename"] == "file2.py"].iloc[0]
            assert file2_row["smells"] == 1
            assert file2_row["loc"] == 20
            # Float comparison safety
            assert abs(file2_row["density"] - 0.05) < 1e-9
            assert file2_row["quality"] == "High"

    assert found_files_sheet, "Did not find a call to to_excel with a Files sheet"
