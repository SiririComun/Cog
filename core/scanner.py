#!/usr/bin/env python3
"""
Cog: Repository Artifact Scanner (scanner.py)
Traverses codebase trees, prunes noise via IgnoreFilter, and classifies
hardware, software, build scripts, and documentation files into domain buckets.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# Ensure core directory is on sys.path for sibling imports
CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from ignore_matcher import IgnoreFilter


class RepoScanner:
    """
    Scans a repository tree and categorizes files into functional engineering domains.
    """

    # Primary extension mappings
    RTL_EXTS = {".vhd", ".vhdl", ".v", ".sv"}
    BD_EXTS = {".bd"}
    CONSTRAINTS_EXTS = {".xdc"}
    NOTEBOOK_EXTS = {".ipynb"}
    SOFTWARE_EXTS = {".py", ".c", ".h", ".cpp", ".hpp", ".sh"}
    BUILD_EXTS = {".tcl", ".mk", ".src", ".con", ".sub", ".ext"}
    DOC_EXTS = {".md", ".rst"}

    # Special exact filenames mapped directly to domains
    BUILD_FILENAMES = {"makefile", "cmakelists.txt", "hog.conf"}
    SOFTWARE_FILENAMES = {"setup.py", "pyproject.toml", "requirements.txt"}
    DOC_FILENAMES = {"readme", "license", "authors", "changelog", "contributing"}

    def __init__(
        self,
        repo_root: Path,
        ignore_filter: Optional[IgnoreFilter] = None,
    ):
        self.repo_root = repo_root.resolve()
        self.ignore_filter = ignore_filter or IgnoreFilter(self.repo_root)

    def _is_auto_generated_wrapper(self, file_path: Path, bd_basenames: Set[str]) -> bool:
        """
        Detects if an RTL file is an auto-generated Vivado wrapper for a Block Design
        (e.g., design_1_wrapper.vhd when design_1.bd is present).
        """
        stem = file_path.stem.lower()
        if stem.endswith("_wrapper"):
            bd_candidate = stem[:-8]  # Strip '_wrapper'
            if bd_candidate in bd_basenames:
                return True
        return False

    def scan(self) -> Dict[str, List[str]]:
        """
        Scans the repository and returns files grouped by domain:
        - 'bd'           : Vivado Block Designs
        - 'rtl'          : VHDL, Verilog, SystemVerilog cores
        - 'constraints'  : Vivado .xdc constraint files
        - 'build'        : Hog configs, TCL automation, Makefiles
        - 'software'     : Python drivers, C/C++ libraries, scripts
        - 'notebooks'    : Jupyter Notebook tutorials
        - 'documentation': Markdown docs, LICENSE, README
        """
        categorized: Dict[str, List[str]] = {
            "documentation": [],
            "build": [],
            "bd": [],
            "constraints": [],
            "rtl": [],
            "software": [],
            "notebooks": [],
        }

        discovered_bd_stems: Set[str] = set()
        candidate_rtl_files: List[Path] = []

        # 1. Traverse repository tree
        for current_root, dirnames, files in os_walk_filtered(self.repo_root, self.ignore_filter):
            for filename in files:
                file_path = current_root / filename
                rel_path = file_path.relative_to(self.repo_root)

                # Filter against .gitignore & cog.ignore
                if self.ignore_filter.is_ignored(rel_path):
                    continue

                ext = file_path.suffix.lower()
                stem = file_path.stem.lower()
                fname_lower = filename.lower()
                rel_posix = rel_path.as_posix()

                # Rule 1: Vivado Block Designs
                if ext in self.BD_EXTS:
                    categorized["bd"].append(rel_posix)
                    discovered_bd_stems.add(stem)
                    continue

                # Rule 2: Constraints
                if ext in self.CONSTRAINTS_EXTS:
                    categorized["constraints"].append(rel_posix)
                    continue

                # Rule 3: Jupyter Notebooks
                if ext in self.NOTEBOOK_EXTS:
                    categorized["notebooks"].append(rel_posix)
                    continue

                # Rule 4: Build automation & Hog configurations
                if (
                    ext in self.BUILD_EXTS
                    or fname_lower in self.BUILD_FILENAMES
                    or "hog.conf" in fname_lower
                ):
                    categorized["build"].append(rel_posix)
                    continue

                # Rule 5: Root Documentation & Licenses
                if ext in self.DOC_EXTS or stem in self.DOC_FILENAMES:
                    categorized["documentation"].append(rel_posix)
                    continue

                # Rule 6: Hardware RTL (Deferred to filter auto-generated wrappers)
                if ext in self.RTL_EXTS:
                    candidate_rtl_files.append(file_path)
                    continue

                # Rule 7: Software, drivers & packaging
                if ext in self.SOFTWARE_EXTS or fname_lower in self.SOFTWARE_FILENAMES:
                    categorized["software"].append(rel_posix)
                    continue

        # 2. Filter candidate RTL files against auto-generated wrappers
        for rtl_path in candidate_rtl_files:
            if not self._is_auto_generated_wrapper(rtl_path, discovered_bd_stems):
                rel_posix = rtl_path.relative_to(self.repo_root).as_posix()
                categorized["rtl"].append(rel_posix)

        # 3. Deterministically sort all category lists
        for cat in categorized:
            categorized[cat].sort()

        return categorized

    def get_ordered_targets(self) -> List[str]:
        """
        Returns all categorized targets in logical architectural order:
        Documentation -> Build -> Block Design -> Constraints -> RTL -> Software -> Notebooks.
        """
        scan_results = self.scan()
        ordered: List[str] = []
        for section in (
            "documentation",
            "build",
            "bd",
            "constraints",
            "rtl",
            "software",
            "notebooks",
        ):
            ordered.extend(scan_results[section])
        return list(dict.fromkeys(ordered))


def os_walk_filtered(root: Path, ignore_filter: IgnoreFilter):
    """
    Helper generator that performs os.walk while pruning ignored directories early.
    """
    import os

    for current_root_str, dirnames, filenames in os.walk(root):
        current_root = Path(current_root_str)

        try:
            rel_dir = current_root.relative_to(root)
            if rel_dir != Path(".") and ignore_filter.is_ignored(rel_dir):
                dirnames.clear()
                continue
        except ValueError:
            pass

        # Prune ignored child directories in-place before descending
        dirnames[:] = [
            d
            for d in dirnames
            if not ignore_filter.is_ignored(
                (current_root / d).relative_to(root)
            )
        ]

        yield current_root, dirnames, filenames