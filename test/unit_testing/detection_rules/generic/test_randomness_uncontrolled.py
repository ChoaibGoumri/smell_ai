import ast
import pytest
from detection_rules.generic.randomness_uncontrolled import (
    RandomnessUncontrolledSmell,
)


@pytest.fixture
def smell_detector():
    """
    Fixture to initialize the RandomnessUncontrolledSmell instance.
    """
    return RandomnessUncontrolledSmell()


def test_detect_no_smell(smell_detector):
    """
    Test the detect method when randomness is properly controlled.
    """
    code = (
        "from sklearn.ensemble import RandomForestClassifier\n"
        "from sklearn.model_selection import train_test_split\n"
        "def main():\n"
        "    rf = RandomForestClassifier(random_state=42)\n"
        "    data = [1, 2, 3]\n"
        "    train, test = train_test_split(data, random_state=123)\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "models": {
            "library": ["sklearn"],
            "method": ["RandomForestClassifier"]
        }
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 0  # No smells should be detected


def test_detect_model_instantiation_without_seed(smell_detector):
    """
    Test detecting smell when ML model is instantiated without random_state.
    """
    code = (
        "from sklearn.ensemble import RandomForestClassifier\n"
        "def main():\n"
        "    rf = RandomForestClassifier(n_estimators=100)\n"
    )
    tree = ast.parse(code)
    extracted_data = {
         "models": {
            "library": ["sklearn"],
            "method": ["RandomForestClassifier"]
        }
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 1
    assert result[0]["name"] == "Randomness Uncontrolled"
    assert "RandomForestClassifier" in result[0]["additional_info"]


def test_detect_sensitive_function_without_seed(smell_detector):
    """
    Test detecting smell when sensitive function like train_test_split is used without seed.
    """
    code = (
        "from sklearn.model_selection import train_test_split\n"
        "def main():\n"
        "    data = [1, 2, 3]\n"
        "    train, test = train_test_split(data, test_size=0.2)\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "models": {} 
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 1
    assert result[0]["name"] == "Randomness Uncontrolled"
    assert "train_test_split" in result[0]["additional_info"]


def test_detect_unknown_model_no_smell(smell_detector):
    """
    Test that unknown functions/classes are ignored.
    """
    code = (
        "def main():\n"
        "    unknown = SomeUnknownClass()\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "models": {}
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 0
