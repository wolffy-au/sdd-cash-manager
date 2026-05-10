#!/usr/bin/env python3
"""Enforce architectural layer boundaries for sdd_cash_manager.

Permitted import direction (top → bottom only):
  api       → services, schemas, models, lib, core
  services  → schemas, models, lib, core
  schemas   → models, lib, core
  lib       → models, core
  models    → core
  core      → (nothing internal)
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src" / "sdd_cash_manager"
PKG = "sdd_cash_manager"

LAYERS = ["api", "services", "schemas", "lib", "models", "core"]

# Each layer must not import from these layers.
FORBIDDEN: dict[str, list[str]] = {
    "services": ["api"],
    "schemas": ["api", "services"],
    "lib": ["api", "services"],
    "models": ["api", "services", "schemas"],
    "core": ["api", "services", "schemas", "lib", "models"],
}


def _imported_layers(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    found: set[str] = set()
    for node in ast.walk(tree):
        module = ""
        level = 0
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                for i, part in enumerate(parts):
                    if part in LAYERS and (i == 0 or parts[i - 1] == PKG):
                        found.add(part)
            continue

        if not module:
            continue

        parts = module.split(".")
        for i, part in enumerate(parts):
            if part in LAYERS:
                # Absolute import: sdd_cash_manager.<layer>
                # Relative import: level > 0 means we're inside the package
                if level > 0 or i == 0 or parts[i - 1] == PKG:
                    found.add(part)
                break

    return list(found)


def main() -> int:
    violations: list[str] = []

    for layer, forbidden_layers in FORBIDDEN.items():
        layer_dir = ROOT / layer
        if not layer_dir.exists():
            continue
        for py_file in sorted(layer_dir.rglob("*.py")):
            for imp_layer in _imported_layers(py_file):
                if imp_layer in forbidden_layers:
                    rel = py_file.relative_to(ROOT.parent.parent)
                    violations.append(f"  {rel}: '{layer}' must not import from '{imp_layer}'")

    if violations:
        print("❌ Layer boundary violations detected:")
        for v in violations:
            print(v)
        return 1

    print("✅ Layer boundaries OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
