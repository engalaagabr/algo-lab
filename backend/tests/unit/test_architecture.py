"""Guard the inward import boundaries that make new algorithm modules independent."""

import ast
import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "layer,allowed_packages",
    [
        ("domain", ("domain",)),
        ("application", ("application", "domain")),
        ("algorithms", ("algorithms", "domain")),
    ],
)
def test_inner_layers_only_import_standard_library_and_inward_packages(
    layer: str,
    allowed_packages: tuple[str, ...],
) -> None:
    root = Path(__file__).resolve().parents[2] / "src"
    violations: list[str] = []
    for source in (root / layer).rglob("*.py"):
        package = ".".join(source.parent.relative_to(root).parts)
        for node in ast.walk(ast.parse(source.read_text(), filename=str(source))):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    module = importlib.util.resolve_name("." * node.level + module, package)
                imported = [f"{module}.{alias.name}" for alias in node.names]
            for name in imported:
                is_stdlib = name.split(".")[0] in sys.stdlib_module_names
                is_inward = any(
                    name == allowed or name.startswith(allowed + ".")
                    for allowed in allowed_packages
                )
                if not is_stdlib and not is_inward:
                    violations.append(f"{source.relative_to(root)}:{node.lineno}: {name}")
    assert not violations, "Forbidden imports across architecture boundaries:\n" + "\n".join(
        violations
    )
