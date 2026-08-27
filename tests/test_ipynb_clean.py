#!/usr/bin/env python3
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from ipynb_clean import NotebookCleaner


class TestNotebookCleaner(unittest.TestCase):
    def test_strips_binary_outputs_and_keeps_code(self):
        mock_nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": 5,
                    "source": ["from pynq import Overlay\n", "ol = Overlay('test.bit')"],
                    "outputs": [{"output_type": "display_data", "data": {"image/png": "base64blob"}}]
                }
            ]
        }
        cleaned = NotebookCleaner.clean_notebook(json.dumps(mock_nb))

        self.assertIn("# %% [code] Cell 1 [In 5]", cleaned)
        self.assertIn("from pynq import Overlay", cleaned)
        self.assertNotIn("base64blob", cleaned)

    def test_preserves_safety_critical_warnings(self):
        mock_nb = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": [
                        "This paragraph is quite long and describes tutorial setup steps. "
                        "WARNING: Exceeding 3.3V on pin AD0 will damage the analog front-end ADC! "
                        "Make sure to ground the circuit before turning on the power supply."
                    ]
                },
                {
                    "cell_type": "markdown",
                    "source": [
                        "| Pin | Signal |\n",
                        "| :--- | :--- |\n",
                        "| A0 | VAUX_P |"
                    ]
                }
            ]
        }
        cleaned = NotebookCleaner.clean_notebook(json.dumps(mock_nb))

        self.assertIn("WARNING: Exceeding 3.3V on pin AD0", cleaned)
        self.assertIn("| Pin | Signal |", cleaned)


if __name__ == "__main__":
    unittest.main()