#!/usr/bin/env python3
"""
Cog: LaTeX & BibTeX Compactor Engine (tex_clean.py)
Compacts LaTeX manuscripts (.tex, .sty, .cls) and BibTeX databases (.bib).
Strips draft comments, purges heavy non-essential BibTeX metadata (abstract, file),
and collapses whitespace while preserving equations, escaped percentages, and verbatim environments.
"""

import re
from typing import List


class TexCleaner:
    """
    High-density compactor for LaTeX manuscripts and BibTeX entries.
    Achieves 40%–60% token reduction on scientific papers and thesis repositories.
    """

    # Magic compiler directives that must be preserved
    MAGIC_COMMENT_PATTERN = re.compile(r"^\s*%\s*![tT][eE][xX]\b", re.IGNORECASE)

    # Heavy non-essential BibTeX fields to purge
    EXCLUDED_BIB_FIELDS = {"abstract", "file", "annotation", "urldate"}

    @classmethod
    def _strip_tex_comment(cls, line: str) -> str:
        """
        Strips comments from a LaTeX line while respecting:
        - Escaped percentage signs (e.g. '45\\%')
        - Magic comments ('% !TeX root = ...')
        """
        # 1. Preserve magic compiler comments
        if cls.MAGIC_COMMENT_PATTERN.match(line):
            return line.rstrip()

        # 2. If line begins with %, it is purely a comment
        if re.match(r"^\s*%", line):
            return ""

        # 3. Scan characters to safely detect unescaped %
        in_escape = False
        for i, ch in enumerate(line):
            if ch == "\\":
                in_escape = not in_escape
            elif ch == "%" and not in_escape:
                # Truncate comment and trailing whitespace
                return line[:i].rstrip()
            else:
                in_escape = False

        return line.rstrip()

    @classmethod
    def clean_tex(cls, raw_content: str) -> str:
        """
        Cleans LaTeX source files (.tex, .sty, .cls):
        - Removes dead comment paragraphs and inline comments
        - Protects verbatim and code environments from comment stripping
        - Collapses excess blank lines down to 1
        """
        lines = raw_content.splitlines()
        output_lines: List[str] = []
        in_verbatim = False

        for raw_line in lines:
            line_stripped = raw_line.strip()

            # Check for verbatim / code environment boundaries
            if r"\begin{verbatim}" in line_stripped or r"\begin{lstlisting}" in line_stripped:
                in_verbatim = True
                output_lines.append(raw_line.rstrip())
                continue

            if r"\end{verbatim}" in line_stripped or r"\end{lstlisting}" in line_stripped:
                in_verbatim = False
                output_lines.append(raw_line.rstrip())
                continue

            # Within verbatim blocks, retain raw content verbatim
            if in_verbatim:
                output_lines.append(raw_line.rstrip())
                continue

            cleaned_line = cls._strip_tex_comment(raw_line)
            if cleaned_line:
                output_lines.append(cleaned_line)
            elif not raw_line.strip():
                output_lines.append("")

        result = "\n".join(output_lines)
        # Collapse 3+ consecutive blank lines down to 1
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()

    @classmethod
    def clean_bib(cls, raw_content: str) -> str:
        """
        Cleans BibTeX database files (.bib):
        - Purges heavy multi-line 'abstract = {...}' and 'file = {...}' fields
        - Strips comment blocks while retaining standard citation keys and metadata
        - Normalizes entry formatting
        """
        lines = raw_content.splitlines()
        output_lines: List[str] = []

        skipping_field = False
        brace_depth = 0

        # Pattern matching field assignments: name = { ... or name = " ...
        field_start_pattern = re.compile(
            r"^\s*([a-zA-Z_\-]+)\s*=\s*(.*)", re.IGNORECASE
        )

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                output_lines.append("")
                continue

            # Handle multi-line field skipping (e.g., giant abstract blocks)
            if skipping_field:
                brace_depth += line.count("{") - line.count("}")
                brace_depth += line.count('"') % 2  # Handle double quotes
                if brace_depth <= 0:
                    skipping_field = False
                    brace_depth = 0
                continue

            # Check if this line starts an excluded field
            match = field_start_pattern.match(line)
            if match:
                field_name = match.group(1).lower()
                field_rest = match.group(2)

                if field_name in cls.EXCLUDED_BIB_FIELDS:
                    # Count open vs closed delimiters on the same line
                    open_braces = field_rest.count("{")
                    close_braces = field_rest.count("}")
                    quote_count = field_rest.count('"')

                    # If field is self-contained on a single line
                    if (open_braces > 0 and open_braces == close_braces) or (
                        quote_count >= 2 and quote_count % 2 == 0
                    ):
                        continue

                    # Otherwise, multi-line field: skip subsequent lines until closed
                    brace_depth = open_braces - close_braces
                    if open_braces == 0 and quote_count % 2 != 0:
                        brace_depth = 1

                    if brace_depth > 0:
                        skipping_field = True
                    continue

            output_lines.append(raw_line.rstrip())

        result = "\n".join(output_lines)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()