import ast
import pytest
from detection_rules.generic.hyperparameters_not_explicitly_set import (
    HyperparametersNotExplicitlySetSmell,
)


@pytest.fixture
def smell_detector():
    """
    Fixture to initialize the HyperparametersNotExplicitlySetSmell instance.
    """
    return HyperparametersNotExplicitlySetSmell()


def test_detect_no_smell(smell_detector):
    """
    Test the detect method when all critical hyperparameters are explicitly set.
    """
    code = (
        "import sklearn.ensemble as se\n"
        "def main():\n"
        "    model = se.RandomForestClassifier"
        "(n_estimators=100, max_depth=5)\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": {
            "method": ["RandomForestClassifier()"],
            "library": ["sklearn"],
            "critical_hyperparameters": ["n_estimators"],
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 0  # No smells should be detected


def test_detect_with_smell(smell_detector):
    """
    Test the detect method when critical hyperparameters are not explicitly set.
    """
    code = (
        "import sklearn.ensemble as se\n"
        "def main():\n"
        "    model = se.RandomForestClassifier()\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": {
            "method": ["RandomForestClassifier()"],
            "library": ["sklearn"],
            "critical_hyperparameters": ["n_estimators"],
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 1  # One smell should be detected
    assert result[0]["name"] == "hyperparameters_not_explicitly_set"
    assert "Missing critical configurations: n_estimators" in result[0]["additional_info"]
    assert result[0]["line"] == 3  # Line where the smell occurs


def test_detect_partial_smell(smell_detector):
    """
    Test the detect method when some parameters are set but critical ones are missing.
    """
    code = (
        "import sklearn.ensemble as se\n"
        "def main():\n"
        "    model = se.RandomForestClassifier(max_depth=5)\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": {
            "method": ["RandomForestClassifier()"],
            "library": ["sklearn"],
            "critical_hyperparameters": ["n_estimators"],
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 1  # One smell should be detected
    assert "Missing critical configurations: n_estimators" in result[0]["additional_info"]


def test_detect_without_library(smell_detector):
    """
    Test the detect method when the library is not imported.
    """
    code = (
        "\n"
        "\n"
        "def main():\n"
        "\n"
        "    model1 = RandomForestClassifier()\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {},
        "models": {
            "method": ["RandomForestClassifier()"],
            "library": ["sklearn"],
            "critical_hyperparameters": ["n_estimators"],
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 0  # No smells should be detected


def test_detect_with_multiple_smells(smell_detector):
    """
    Test the detect method when multiple
    models are defined without critical hyperparameters.
    """
    code = (
        "import sklearn.ensemble as se\n"
        "def main():\n"
        "    model1 = se.RandomForestClassifier()\n"
        "    model2 = se.GradientBoostingClassifier()\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": {
            "method": [
                "RandomForestClassifier()",
                "GradientBoostingClassifier()",
            ],
            "library": ["sklearn", "sklearn"],
            "critical_hyperparameters": ["n_estimators", "n_estimators"],
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 2  # Two smells should be detected
    assert result[0]["line"] == 3  # Line of the first smell
    assert result[1]["line"] == 4  # Line of the second smell


def test_detect_with_no_critical_params(smell_detector):
    """
    Test when a model has no critical hyperparameters defined (should skip).
    """
    code = (
        "import sklearn.ensemble as se\n"
        "def main():\n"
        "    model = se.SomeModel()\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": {
            "method": ["SomeModel()"],
            "library": ["sklearn"],
            "critical_hyperparameters": [""],  # Empty string, no critical params
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 0  # Should skip models without critical params


def test_detect_with_positional_args(smell_detector):
    """
    Test when model is instantiated with positional arguments (should skip).
    """
    code = (
        "import sklearn.ensemble as se\n"
        "def main():\n"
        "    model = se.RandomForestClassifier(100)\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": {
            "method": ["RandomForestClassifier()"],
            "library": ["sklearn"],
            "critical_hyperparameters": ["n_estimators"],
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 0  # Should skip when positional args are used


def test_detect_with_non_alias_import(smell_detector):
    """
    Test when library is imported without alias.
    """
    code = (
        "from sklearn.ensemble import RandomForestClassifier\n"
        "def main():\n"
        "    model = RandomForestClassifier()\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {"sklearn": "sklearn"},  # No alias
        "models": {
            "method": ["RandomForestClassifier()"],
            "library": ["sklearn"],
            "critical_hyperparameters": ["n_estimators"],
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 1
    assert "RandomForestClassifier" in result[0]["additional_info"]


def test_get_full_function_name_with_direct_name(smell_detector):
    """
    Test _get_full_function_name when func is a simple ast.Name (no alias).
    """
    code = "RandomForestClassifier()"
    tree = ast.parse(code)
    call_node = tree.body[0].value
    
    libraries = {"sklearn": "se"}
    func_name = smell_detector._get_full_function_name(call_node.func, libraries)
    
    assert func_name == "RandomForestClassifier"


def test_detect_with_non_string_critical_params(smell_detector):
    """
    Test when critical_hyperparameters is not a string (edge case).
    """
    code = (
        "import sklearn.ensemble as se\n"
        "def main():\n"
        "    model = se.RandomForestClassifier()\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": {
            "method": ["RandomForestClassifier()"],
            "library": ["sklearn"],
            "critical_hyperparameters": [None],  # Non-string value
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 0  # Should handle gracefully


def test_detect_with_empty_models_data(smell_detector):
    """
    Test when models_data is empty or missing required keys.
    """
    code = (
        "import sklearn.ensemble as se\n"
        "def main():\n"
        "    model = se.RandomForestClassifier()\n"
    )
    tree = ast.parse(code)
    
    # Test with empty models dict
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": {}  # Missing 'method' and 'critical_hyperparameters' keys
    }
    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 0
    
    # Test with None models
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": None
    }
    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 0


def test_detect_unknown_model_method(smell_detector):
    """
    Test when a model method is called that is not in the critical params map.
    """
    code = (
        "import sklearn.ensemble as se\n"
        "def main():\n"
        "    model = se.UnknownModel()\n"
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": {
            "method": ["RandomForestClassifier()"],  # Different from UnknownModel
            "library": ["sklearn"],
            "critical_hyperparameters": ["n_estimators"],
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 0  # UnknownModel not tracked, so no smell


def test_get_full_function_name_with_non_alias(smell_detector):
    """
    Test _get_full_function_name when func.id is NOT in libraries.values().
    This covers the else branch at line 140.
    """
    # Create AST for: SomeModule.SomeClass()
    # where SomeModule is NOT an alias in libraries
    name_node = ast.Name(id='SomeModule', ctx=ast.Load())
    attr_node = ast.Attribute(value=name_node, attr='SomeClass', ctx=ast.Load())
    
    libraries = {"sklearn": "sk", "numpy": "np"}  # SomeModule is not here
    func_name = smell_detector._get_full_function_name(attr_node, libraries)
    
    # Should return the name as-is since SomeModule is not an alias
    assert func_name == "SomeModule.SomeClass"


def test_get_full_function_name_with_alias_match(smell_detector):
    """
    Test _get_full_function_name when func.id IS in libraries.values() (is an alias).
    This specifically tests the branch where func.id is in libraries.values()
    and the code resolves the alias to the original library name.
    """
    # Create an AST manually to ensure we hit the exact code path
    # Create: sk.ensemble.RandomForestClassifier()
    # where sk is alias for sklearn
    
    # Build the AST: sk.ensemble.RandomForestClassifier
    name_node = ast.Name(id='sk', ctx=ast.Load())
    attr1 = ast.Attribute(value=name_node, attr='ensemble', ctx=ast.Load())
    attr2 = ast.Attribute(value=attr1, attr='RandomForestClassifier', ctx=ast.Load())
    
    libraries = {"sklearn": "sk"}  # "sk" is the alias for "sklearn"
    func_name = smell_detector._get_full_function_name(attr2, libraries)
    
    # Should resolve the alias and return the full name
    assert func_name == "sklearn.ensemble.RandomForestClassifier"


def test_detect_with_library_alias_full_integration(smell_detector):
    """
    Full integration test to ensure alias resolution works in the detect method.
    This should exercise the _get_full_function_name with an alias.
    """
    code = (
        "import sklearn.ensemble as se\n"
        "def main():\n"
        "    model = se.RandomForestClassifier(max_depth=5)\n"  # Missing n_estimators
    )
    tree = ast.parse(code)
    extracted_data = {
        "libraries": {"sklearn": "se"},
        "models": {
            "method": ["RandomForestClassifier()"],
            "library": ["sklearn"],
            "critical_hyperparameters": ["n_estimators"],
        },
    }

    result = smell_detector.detect(tree, extracted_data)
    assert len(result) == 1
    # Verify that the alias was correctly resolved in the error message
    assert "sklearn" in result[0]["additional_info"] or "se" in result[0]["additional_info"]


def test_get_full_function_name_with_non_name_node(smell_detector):
    """
    Test _get_full_function_name when func is neither ast.Name nor ast.Attribute.
    This covers the case where isinstance(func, ast.Name) is False,
    triggering the branch 132->141 (skipping to return).
    """
    # Create a complex function call like: (lambda x: x)()
    # The func here is a Lambda, not a Name or Attribute
    lambda_node = ast.Lambda(
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg='x', annotation=None)],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[]
        ),
        body=ast.Name(id='x', ctx=ast.Load())
    )
    
    libraries = {"sklearn": "sk"}
    func_name = smell_detector._get_full_function_name(lambda_node, libraries)
    
    # Should return empty string since it's not a Name or Attribute chain
    assert func_name == ""
