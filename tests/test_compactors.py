#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from c_slicer import CSlicer
from tcl_clean import TclCleaner
from xdc_clean import XdcCleaner


class TestSpecializedCompactors(unittest.TestCase):
    def test_xdc_consolidation_and_pruning(self):
        raw_xdc = """
# Vivado Generated Constraints
# Tool Version: Vivado 2024.2
set_property PACKAGE_PIN R14 [get_ports {led[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[0]}]
# Inactive commented pins
# set_property PACKAGE_PIN M20 [get_ports {sw[0]}]
create_clock -period 10.000 [get_ports sys_clk]
"""
        cleaned = XdcCleaner.clean_xdc(raw_xdc)

        self.assertIn("set_property -dict { PACKAGE_PIN R14 IOSTANDARD LVCMOS33 } [get_ports {led[0]}]", cleaned)
        self.assertIn("create_clock -period 10.000 [get_ports sys_clk]", cleaned)
        self.assertNotIn("sw[0]", cleaned)
        self.assertNotIn("Vivado Generated Constraints", cleaned)

    def test_tcl_session_header_stripping(self):
        raw_tcl = """
# Vivado (TM) v2024.2 (64-bit)
# Start of session at: Wed Aug 26 14:00:00 2026
# Process ID: 12345
create_project my_proj ./build -part xc7z020clg400-1
set_property target_language VHDL [current_project]
"""
        cleaned = TclCleaner.clean_tcl(raw_tcl)

        self.assertIn("create_project my_proj", cleaned)
        self.assertIn("set_property target_language VHDL", cleaned)
        self.assertNotIn("Vivado (TM)", cleaned)
        self.assertNotIn("Process ID:", cleaned)

    def test_c_slicer_license_stripping(self):
        raw_c = """
/*
 * Copyright (C) 2010 - 2026 Xilinx, Inc. All rights reserved.
 * Permission is hereby granted, free of charge...
 */
#define XADC_CR_OFFSET 0x00000000
typedef struct { uint32_t base; } xadc_dev_t;
int xadc_init(xadc_dev_t *dev);
"""
        cleaned = CSlicer.slice_c_cpp(raw_c, ".h")

        self.assertIn("#define XADC_CR_OFFSET 0x00000000", cleaned)
        self.assertIn("typedef struct { uint32_t base; } xadc_dev_t;", cleaned)
        self.assertIn("int xadc_init(xadc_dev_t *dev);", cleaned)
        self.assertNotIn("Copyright (C) 2010", cleaned)
        self.assertNotIn("Permission is hereby granted", cleaned)


if __name__ == "__main__":
    unittest.main()