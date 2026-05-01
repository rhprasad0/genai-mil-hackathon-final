from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from policy_bonfire.import_policy import FORBIDDEN_IMPORT_ROOTS, scan_forbidden_imports


class ImportPolicyTests(unittest.TestCase):
    def test_policy_bonfire_has_no_forbidden_imports(self):
        package_dir = Path(__file__).resolve().parents[1] / "policy_bonfire"
        self.assertEqual([], scan_forbidden_imports(package_dir))

    def test_scanner_catches_deferred_imports(self):
        source = "def f():\n    import requests\n"
        tree = ast.parse(source)
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
        self.assertTrue(any(name in FORBIDDEN_IMPORT_ROOTS for name in names))
    def test_live_adapter_boundary_allows_provider_imports_only_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "policy_bonfire"
            adapters = root / "live_adapters"
            adapters.mkdir(parents=True)
            (root / "core.py").write_text("import requests\n", encoding="utf-8")
            (adapters / "provider.py").write_text("import requests\nimport openai\n", encoding="utf-8")
            findings = scan_forbidden_imports(root)
            self.assertEqual(1, len(findings))
            self.assertTrue(findings[0]["path"].endswith("core.py"))


if __name__ == "__main__":
    unittest.main()
