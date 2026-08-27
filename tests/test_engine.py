#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from engine import CogEngine
from token_meter import TokenMeter


class TestEngineAndTokenMeter(unittest.TestCase):
    def test_token_meter_calibrated_ratio(self):
        sample_text = "a" * 362
        est = TokenMeter.estimate_tokens(sample_text)
        self.assertEqual(est, 100)

    def test_token_meter_tier_compatibility(self):
        badge, _ = TokenMeter.get_model_compatibility(15000)
        self.assertIn("Universal", badge)

        badge, _ = TokenMeter.get_model_compatibility(75000)
        self.assertIn("Standard", badge)

        badge, _ = TokenMeter.get_model_compatibility(160000)
        self.assertIn("Extended", badge)

        badge, _ = TokenMeter.get_model_compatibility(250000)
        self.assertIn("Ultra-Large", badge)

    def test_engine_glob_resolution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            conf_dir = root / "context" / "conf"
            conf_dir.mkdir(parents=True)

            # Create mock files
            (root / "src").mkdir()
            (root / "src" / "test1.py").touch()
            (root / "src" / "test2.py").touch()

            # Create cog.conf
            cog_conf = conf_dir / "cog.conf"
            with open(cog_conf, "w", encoding="utf-8") as f:
                f.write("OUTPUT: context/test.txt\nsrc/*.py\n")

            engine = CogEngine(root)
            targets, _ = engine.parse_config()

            self.assertEqual(len(targets), 2)
            self.assertIn("src/test1.py", targets)
            self.assertIn("src/test2.py", targets)


if __name__ == "__main__":
    unittest.main()