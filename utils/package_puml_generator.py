import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def find_python_files(package_dir: Path) -> List[Path]:
    files: List[Path] = []
    for root, dirs, filenames in os.walk(package_dir):
        # skip __pycache__ and hidden folders
        dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".py") and fn != "__init__.py":
                files.append(Path(root) / fn)
    return files


class ClassInfo:
    def __init__(self, module: str, name: str, bases: List[str], methods: List[str]):
        self.module = module
        self.name = name
        self.bases = bases
        self.methods = methods

    @property
    def fqname(self) -> str:
        return f"{self.module}.{self.name}" if self.module else self.name

    @property
    def alias(self) -> str:
        # Provide a PlantUML-safe alias (unique per class in package)
        return (self.module + "_" + self.name).replace(".", "_") if self.module else self.name


def _base_name(node: ast.AST) -> Optional[str]:
    # Extract the rightmost identifier of a base class expression
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        # walk attribute chain to rightmost name
        parts = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        parts = list(reversed(parts))
        return parts[-1] if parts else None
    if isinstance(node, ast.Subscript):
        # e.g., Generic[T]; take the value part
        return _base_name(node.value)
    return None


def parse_classes(py_file: Path, package_dir: Path) -> List[ClassInfo]:
    try:
        source = py_file.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except Exception:
        return []

    module = py_file.relative_to(package_dir).with_suffix("")
    module_str = ".".join(module.parts)

    classes: List[ClassInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = []
            for b in node.bases:
                name = _base_name(b)
                if name:
                    bases.append(name)
            methods: List[str] = []
            for body in node.body:
                if isinstance(body, ast.FunctionDef):
                    methods.append(body.name)
            classes.append(ClassInfo(module=module_str, name=node.name, bases=bases, methods=methods))
    return classes


def build_puml_for_package(package_name: str, root: Path) -> Tuple[str, List[ClassInfo]]:
    package_dir = root / package_name
    if not package_dir.exists() or not package_dir.is_dir():
        raise FileNotFoundError(f"Package directory not found: {package_dir}")

    py_files = find_python_files(package_dir)
    all_classes: List[ClassInfo] = []
    for f in py_files:
        all_classes.extend(parse_classes(f, package_dir))

    # Index classes by simple name to detect internal inheritance
    by_simple: Dict[str, List[ClassInfo]] = {}
    for c in all_classes:
        by_simple.setdefault(c.name, []).append(c)

    lines: List[str] = []
    lines.append("@startuml")
    lines.append("skinparam classAttributeIconSize 0")
    lines.append(f'package "{package_name}" {{')

    # group by module
    by_module: Dict[str, List[ClassInfo]] = {}
    for c in all_classes:
        by_module.setdefault(c.module, []).append(c)

    for module, classes in sorted(by_module.items()):
        display_module = module.split(".")[-1] if module else package_name
        lines.append(f'  package "{display_module}" {{')
        for c in sorted(classes, key=lambda x: x.name):
            # Represent class with alias so relationships are readable
            header = f'    class "{c.fqname}" as {c.alias} {{'
            lines.append(header)
            # Show first few methods to avoid huge diagrams
            for m in sorted(c.methods)[:12]:
                lines.append(f"      + {m}()")
            if len(c.methods) > 12:
                lines.append("      .. (more) ..")
            lines.append("    }")
        lines.append("  }")

    lines.append("}")

    # inheritance relationships within the same package
    for c in all_classes:
        for b in c.bases:
            targets = by_simple.get(b, [])
            # Connect only to targets from this package to keep diagram scoped
            for t in targets:
                lines.append(f"{c.alias} --|> {t.alias}")

    lines.append("@enduml")
    return "\n".join(lines), all_classes


def write_puml(output_dir: Path, package: str, content: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    # Use simple name for file
    out = output_dir / f"{package}.puml"
    out.write_text(content, encoding="utf-8")
    return out


def main(packages: List[str]) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "package puml"

    for pkg in packages:
        try:
            content, classes = build_puml_for_package(pkg, repo_root)
            path = write_puml(output_dir, pkg, content)
            print(f"Generated {path} with {len(classes)} classes")
        except Exception as e:
            print(f"Failed to generate for '{pkg}': {e}")


if __name__ == "__main__":
    targets = [
        "cli",
        "code_extractor",
        "components",
        "detection_rules",
        "gui",
        "report",
        "utils",
    ]
    main(targets)
