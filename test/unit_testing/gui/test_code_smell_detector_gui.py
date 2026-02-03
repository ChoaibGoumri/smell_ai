import pytest
import tkinter as tk
from unittest.mock import MagicMock, Mock
from gui.code_smell_detector_gui import CodeSmellDetectorGUI


@pytest.fixture
def gui(mocker):
    """
    Fixture to create a tkinter root window
    and initialize the CodeSmellDetectorGUI.
    Mock Tk and other tkinter dialog
    components to avoid errors in headless environments.
    """
    # Create a mock root with all necessary attributes
    mock_root = MagicMock()
    mock_root.tk = MagicMock()
    
    # Mock all tkinter widgets to avoid real GUI creation
    mock_label = mocker.patch("tkinter.Label", return_value=MagicMock())
    mock_button = mocker.patch("tkinter.Button", return_value=MagicMock())
    mock_checkbutton = mocker.patch("tkinter.Checkbutton", return_value=MagicMock())
    mock_spinbox = mocker.patch("tkinter.Spinbox", return_value=MagicMock())
    mock_text = mocker.patch("tkinter.Text", return_value=MagicMock())
    mock_scrollbar = mocker.patch("tkinter.Scrollbar", return_value=MagicMock())
    mock_stringvar = mocker.patch("tkinter.StringVar", return_value=MagicMock())
    mock_boolvar = mocker.patch("tkinter.BooleanVar", return_value=MagicMock())
    
    gui = CodeSmellDetectorGUI(mock_root)
    yield gui


def test_choose_input_path(gui, mocker):
    """
    Test the `choose_input_path` method
    to ensure the input path label is updated.
    """
    mocker.patch(
        "tkinter.filedialog.askdirectory", return_value="/mock/input/path"
    )

    gui.choose_input_path()

    # Verify configure was called with the correct text
    gui.input_path.configure.assert_called_with(text="/mock/input/path")


def test_choose_output_path(gui, mocker):
    """
    Test the `choose_output_path` method to
    ensure the output path label is updated.
    """
    mocker.patch(
        "tkinter.filedialog.askdirectory", return_value="/mock/output/path"
    )

    gui.choose_output_path()

    # Verify configure was called with the correct text
    gui.output_path.configure.assert_called_with(text="/mock/output/path")


def test_run_program_missing_paths(gui, mocker):
    """
    Test the `run_program` method when input or output paths are missing.
    """
    # Configure mock to return "No path selected" for cget("text")
    gui.input_path.cget.return_value = "No path selected"
    gui.output_path.cget.return_value = "No path selected"

    mock_stdout = mocker.patch("sys.stdout", new_callable=mocker.MagicMock)

    gui.run_program()
    output = "".join([call[0][0] for call in mock_stdout.write.call_args_list])
    assert "Error: Please select valid input and output paths." in output


def test_disable_key_press(mocker, gui):
    """
    Test that key presses are disabled in the output Text widget.
    """
    event = mocker.MagicMock()
    result = gui.disable_key_press(event)

    assert result == "break"


def test_gui_layout(gui):
    """
    Test that the GUI layout contains the expected widgets.
    """
    widgets = [
        gui.input_label,
        gui.input_button,
        gui.output_label,
        gui.output_button,
        gui.walker_picker,
        gui.parallel_check,
        gui.resume_check,
        gui.run_button,
        gui.exit_button,
        gui.output_textbox,
    ]

    # Since widgets are mocked, just verify they exist as attributes
    for widget in widgets:
        assert widget is not None
