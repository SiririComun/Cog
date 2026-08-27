#!/usr/bin/env python3
import json
import sys
import unittest
from pathlib import Path

# Ensure core directory is accessible
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from bd_pruner import BlockDesignPruner


class TestBlockDesignPruner(unittest.TestCase):
    def test_purge_layered_metadata(self):
        mock_bd = {
            "design": {
                "components": {
                    "custom_ip_0": {
                        "vlnv": "user.org:user:axis_trigger:1.0",
                        "LAYERED_METADATA": {"huge_struct": [1, 2, 3]},
                        "parameters": {"C_AXIS_TDATA_WIDTH": "32"}
                    }
                }
            }
        }
        pruned_json = BlockDesignPruner.prune_bd_json(json.dumps(mock_bd))
        pruned_data = json.loads(pruned_json)

        self.assertNotIn("LAYERED_METADATA", pruned_data["design"]["components"]["custom_ip_0"])
        self.assertEqual(
            pruned_data["design"]["components"]["custom_ip_0"]["parameters"]["C_AXIS_TDATA_WIDTH"],
            "32"
        )

    def test_prune_ps7_noise_parameters(self):
        mock_bd = {
            "design": {
                "components": {
                    "processing_system7_0": {
                        "vlnv": "xilinx.com:ip:processing_system7:5.5",
                        "parameters": {
                            "PCW_MIO_0_SLEW": "slow",
                            "PCW_DDR_RAM_HIGHADDR": "0x1FFFFFFF",
                            "PCW_USE_S_AXI_HP0": "1"
                        }
                    }
                }
            }
        }
        pruned_json = BlockDesignPruner.prune_bd_json(json.dumps(mock_bd))
        pruned_data = json.loads(pruned_json)
        params = pruned_data["design"]["components"]["processing_system7_0"]["parameters"]

        self.assertNotIn("PCW_MIO_0_SLEW", params)
        self.assertNotIn("PCW_DDR_RAM_HIGHADDR", params)
        self.assertEqual(params.get("PCW_USE_S_AXI_HP0"), "1")


if __name__ == "__main__":
    unittest.main()