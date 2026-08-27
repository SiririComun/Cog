#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from ignore_matcher import IgnoreFilter
from scanner import RepoScanner


class TestScannerAndIgnoreMatcher(unittest.TestCase):
    def test_ignore_filter_default_rules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            filter_engine = IgnoreFilter(root)

            self.assertTrue(filter_engine.is_ignored(Path(".runs/synth_1/runme.log")))
            self.assertTrue(filter_engine.is_ignored(Path("src/__pycache__/core.cpython-310.pyc")))
            self.assertTrue(filter_engine.is_ignored(Path("vivado.jou")))
            self.assertTrue(filter_engine.is_ignored(Path("output.bit")))
            self.assertFalse(filter_engine.is_ignored(Path("src/hdl/top.vhd")))

    def test_scanner_domain_classification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create mock structure
            (root / "sources" / "rtl").mkdir(parents=True)
            (root / "sources" / "rtl" / "alu.vhd").touch()

            (root / "vivado" / "bd").mkdir(parents=True)
            (root / "vivado" / "bd" / "system.bd").touch()
            # Auto-generated wrapper should be excluded from RTL
            (root / "vivado" / "bd" / "system_wrapper.vhd").touch()

            (root / "constraints").mkdir(parents=True)
            (root / "constraints" / "pins.xdc").touch()

            (root / "drivers").mkdir(parents=True)
            (root / "drivers" / "overlay.py").touch()

            scanner = RepoScanner(root)
            results = scanner.scan()

            self.assertIn("sources/rtl/alu.vhd", results["rtl"])
            self.assertNotIn("vivado/bd/system_wrapper.vhd", results["rtl"])
            self.assertIn("vivado/bd/system.bd", results["bd"])
            self.assertIn("constraints/pins.xdc", results["constraints"])
            self.assertIn("drivers/overlay.py", results["software"])


if __name__ == "__main__":
    unittest.main()