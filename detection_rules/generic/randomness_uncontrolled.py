import ast
from detection_rules.smell import Smell

class RandomnessUncontrolledSmell(Smell):
    """
    Detects if ML algorithms or randomness-sensitive functions are used without
    fixing a seed, which leads to non-reproducible results.
    """

    def __init__(self):
        super().__init__(
            name="Randomness Uncontrolled",
            description=(
                "The algorithm involves randomness but no seed/random_state is "
                "fixed. This makes experiments non-reproducible."
            ),
        )
        self.randomness_params = {"random_state", "seed", "random_seed", "shuffle"}

    def detect(
        self, ast_node: ast.AST, extracted_data: dict[str, any]
    ) -> list[dict[str, any]]:
        detected_smells = []
        
        # extracted_data['models'] contains lists of libraries and methods
        # we are interested in the 'method' list
        # keys are e.g. "library", "method"
        models_data = extracted_data.get("models", {})
        model_methods_raw = models_data.get("method", [])
        
        # Clean model names: remove '()' if present
        # e.g. "RandomForestClassifier()" -> "RandomForestClassifier"
        model_names = set()
        for m in model_methods_raw:
            if isinstance(m, str):
                name = m.replace("()", "").strip()
                if name:
                    model_names.add(name)
        
        # Also define a set of standalone functions known to use randomness
        sensitive_functions = {
            "train_test_split",
            "KFold",
            "StratifiedKFold",
            "ShuffleSplit"
        }

        for node in ast.walk(ast_node):
            if isinstance(node, ast.Call):
                function_name = self._get_called_name(node)
                
                # Check if it's a known ML model instantiation or sensitive function
                is_target = (function_name in model_names) or (function_name in sensitive_functions)
                
                if is_target:
                    # Check arguments for randomness control
                    has_seed = False
                    
                    # Check keyword arguments
                    for keyword in node.keywords:
                        if keyword.arg in self.randomness_params:
                            has_seed = True
                            break
                    
                    if not has_seed:
                        detected_smells.append(
                            self.format_smell(
                                line=node.lineno,
                                additional_info=(
                                    f"Function/Class '{function_name}' is used "
                                    f"without a fixed seed (e.g. random_state)."
                                ),
                            )
                        )

        return detected_smells

    def _get_called_name(self, node: ast.Call) -> str:
        """Helper to get the name of the called function/class."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""
