#!/usr/bin/env python3
"""
Cog: Vivado & Hog TCL Build Script Compactor (tcl_clean.py)
Strips auto-generated Vivado session headers, execution logs, and disclaimer boilerplate
while preserving 100% of project configurations, parts, IP paths, and build strategies.
"""

import re
from typing import List


class TclCleaner:
    """
    High-density compactor for Vivado, Vitis, and Hog TCL build scripts (.tcl).
    Reduces 30%–50% of TCL script tokens by removing tool session noise.
    """

    # Vivado auto-generated session comments and metadata
    TOOL_SESSION_PATTERNS = [
        re.compile(r"^\s*#\s*Vivado\s+\(TM\)\s+v\d+.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*(SW|IP)\s+Build\s+\d+.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*SharedData\s+Build\s+.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*Start\s+of\s+session\s+at:.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*Process\s+ID\s*:\s*\d+.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*Current\s+directory\s*:.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*Command\s+line\s*:.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*Log\s+file\s*:.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*Journal\s+file\s*:.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*Copyright\s+1986-20\d{2}\s+Xilinx,?\s+Inc\..*", re.IGNORECASE),
        re.compile(r"^\s*#\s*Copyright\s+2022-20\d{2}\s+Advanced\s+Micro\s+Devices,?\s+Inc\..*", re.IGNORECASE),
    ]

    # Reusable disclaimer / how-to-run boilerplate blocks
    DISCLAIMER_PATTERNS = [
        re.compile(r"^\s*#\s*This\s+file\s+contains\s+the\s+Vivado\s+Tcl\s+script\s+for\s+re-creating.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*To\s+re-create\s+the\s+project,\s+launch\s+Vivado\s+in\s+batch\s+mode.*", re.IGNORECASE),
        re.compile(r"^\s*#\s*open\s+Vivado,\s+then\s+source\s+this\s+script\s+file.*", re.IGNORECASE),
    ]

    @classmethod
    def clean_tcl(cls, raw_content: str) -> str:
        """
        Cleans TCL build script content by removing tool execution logs and header comments.
        """
        lines = raw_content.splitlines()
        output_lines: List[str] = []

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                output_lines.append("")
                continue

            # 1. Strip tool session metadata
            if any(pat.match(line) for pat in cls.TOOL_SESSION_PATTERNS):
                continue

            # 2. Strip standard Vivado project recreation instructions
            if any(pat.match(line) for pat in cls.DISCLAIMER_PATTERNS):
                continue

            # 3. Preserve structural section comments and executable TCL commands
            output_lines.append(raw_line.rstrip())

        # Collapse excess blank lines (3+ consecutive blank lines down to 1)
        result = "\n".join(output_lines)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()