import ast
from detection_rules.smell import Smell


class HyperparametersNotExplicitlySetSmell(Smell):
    """
    Detects cases where hyperparameters are not
    explicitly set when defining models.

    Example of code smell:
        model = Model()  # No hyperparameters set

    Preferred alternative:
        model = Model(hyperparameter=value)  # Explicitly set hyperparameters
    """

    def __init__(self):
        super().__init__(
            name="hyperparameters_not_explicitly_set",
            description=(
                "Hyperparameters should be explicitly set when defining "
                "models to ensure clarity and reproducibility."
            ),
        )

    def detect(
        self, ast_node: ast.AST, extracted_data: dict[str, any]
    ) -> list[dict[str, any]]:

        smells = []

        # Retrieve model methods and libraries
        model_methods = extracted_data.get("model_methods", [])
        libraries = extracted_data.get("libraries", {})

        if not libraries:
            return smells

        # Build a map of model method/class names to their critical hyperparameters
        # Key: method_name (e.g., 'RandomForestClassifier'), Value: set of critical params
        method_critical_params = {}
        
        models_data = extracted_data.get("models", {})
        if (
            models_data 
            and "method" in models_data 
            and "critical_hyperparameters" in models_data
        ):
            methods = models_data["method"]
            critical_params_list = models_data["critical_hyperparameters"]
            
            for method, params_str in zip(methods, critical_params_list):
                # Normalize method name (remove '()')
                norm_method = method.replace("()", "")
                
                # Parse comma-separated params
                if params_str and isinstance(params_str, str):
                    params = {p.strip() for p in params_str.split(",") if p.strip()}
                else:
                    params = set()
                
                method_critical_params[norm_method] = params

        # Traverse AST to find calls to model definitions
        for node in ast.walk(ast_node):
            if isinstance(node, ast.Call):
                # Extract the full function name
                func_name = self._get_full_function_name(node.func, libraries)

                # Match the function name with known models
                base_func_name = func_name.split(".")[-1]
                
                if base_func_name in method_critical_params:
                    required_params = method_critical_params[base_func_name]
                    
                    # If this model has no critical params defined, we skip it
                    # (Or we could enforce checking even if list is empty? 
                    # CR says "check presence of params relative to critical hyperparameters")
                    if not required_params:
                        continue
                        
                    # Check if positional args are used
                    if node.args:
                        # If positional args are present, we assume the user is explicitly
                        # setting parameters (but using position). We might miss a smell
                        # if they missed a critical param that is further down the list,
                        # but we avoid false positives on 'Model(100)'.
                        # Ideally, we should check signature, but we don't have it.
                        continue
                    
                    # Check keyword args
                    provided_keywords = {
                        kw.arg for kw in node.keywords if kw.arg
                    }
                    
                    missing_params = required_params - provided_keywords
                    
                    if missing_params:
                        missing_str = ", ".join(sorted(missing_params))
                        smells.append(
                            self.format_smell(
                                line=node.lineno,
                                additional_info=(
                                    f"Hyperparameters not explicitly set for model "
                                    f"'{func_name}'. Missing critical configurations: "
                                    f"{missing_str}. Defaults may change "
                                    "in library updates."
                                ),
                            )
                        )

        return smells

    def _get_full_function_name(self, func: ast.AST, libraries: dict) -> str:
        """
        Extracts the full name of a function or method from
        an AST node, handling library aliases.

        Parameters:
        - func: The AST node representing the function or method.
        - libraries: Dictionary of library aliases from extracted_data.

        Returns:
        - str: The full name of the function
          (e.g., "sklearn.ensemble.RandomForestClassifier").
        """
        names = []
        while isinstance(func, ast.Attribute):
            names.append(func.attr)
            func = func.value

        if isinstance(func, ast.Name):
            # Handle aliases for libraries
            if func.id in libraries.values():
                alias = next(
                    key for key, value in libraries.items() if value == func.id
                )
                names.append(alias)
            else:
                names.append(func.id)
        return ".".join(reversed(names))
