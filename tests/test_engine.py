#!/usr/bin/env python3
import sys
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
        repo_root = Path(__file__).resolve().parent.parent
        engine = CogEngine(repo_root)
        targets, _ = engine.parse_config()
        self.assertGreater(len(targets), 0)


if __name__ == "__main__":
    unittest.main()