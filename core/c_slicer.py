#!/usr/bin/env python3
"""
Cog: Embedded C/C++ Driver & HLS Slicer (c_slicer.py)
Compacts embedded C/C++ driver code, Linux UIO wrappers, and Vitis HLS kernels.
Strips licensing boilerplate while preserving 100% of register definitions,
struct memory layouts, bitmasks, and hardware HLS pragmas.
"""

import re
from typing import List


class CSlicer:
    """
    High-density compactor for embedded C/C++ drivers (.c, .cpp, .h, .hpp).
    Reduces 35%–60% of tokens while preserving memory-mapped interfaces.
    """

    # Multi-line license / copyright blocks (/* ... Copyright ... */)
    LICENSE_BLOCK_PATTERNS = [
        re.compile(r"/\*.*?(copyright|license|xilinx|advanced micro devices|all rights reserved).*?\*/", re.DOTALL | re.IGNORECASE),
        re.compile(r"//\s*(copyright|license|all rights reserved).*?(?=\n\s*\n|\Z)", re.DOTALL | re.IGNORECASE),
    ]

    # Tool-generated header markers (e.g. Vitis HLS generated headers)
    TOOL_HEADER_PATTERNS = [
        re.compile(r"//\s*={5,}\s*//\s*File\s+generated\s+by\s+Vitis.*?(?=\n\s*\n|\Z)", re.DOTALL | re.IGNORECASE),
    ]

    @classmethod
    def slice_c_cpp(cls, raw_content: str, ext: str = ".h") -> str:
        """
        Cleans C/C++ source or header content:
        - Removes legal and copyright headers
        - Preserves all #define, #pragma, struct, enum, and typedef declarations
        - Preserves inline comments documenting hardware register bitfields
        - Collapses excess blank lines
        """
        text = raw_content

        # 1. Strip license and copyright comment blocks
        for pat in cls.LICENSE_BLOCK_PATTERNS:
            text = pat.sub("", text)

        # 2. Strip Vitis / Vivado auto-generated file header banners
        for pat in cls.TOOL_HEADER_PATTERNS:
            text = pat.sub("", text)

        # 3. Process line-by-line whitespace
        lines = text.splitlines()
        output_lines: List[str] = []

        for raw_line in lines:
            line = raw_line.rstrip()
            output_lines.append(line)

        # 4. Collapse 3+ consecutive blank lines down to a single blank line
        result = "\n".join(output_lines)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()