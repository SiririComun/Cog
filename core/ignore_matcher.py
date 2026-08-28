#!/usr/bin/env python3
"""
Cog: Ignore Pattern Engine (ignore_matcher.py)
Filters files and directories against default EDA/Python noise,
repository .gitignore rules, and Cog-specific cog.ignore files.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple


class IgnoreFilter:
    """
    Evaluates relative file paths against default EDA exclusions,
    submodule boundaries (.gitmodules), repository .gitignore rules,
    and user-defined cog.ignore files.
    """

    # Built-in EDA, submodule, hardware build artifact, and software noise defaults
    DEFAULT_IGNORE_PATTERNS = [
        # Git & Submodules
        ".git",
        ".git/**",
        ".cog",
        ".cog/**",
        "Cog",
        "Cog/**",
        "Hog",
        "Hog/**",
        # Vivado / EDA Artifacts & Logs
        "**/.runs/**",
        "**/.cache/**",
        "**/.sim/**",
        "**/.hw/**",
        "**/.ip_user_files/**",
        "**/*.jou",
        "**/*.log",
        "**/*.str",
        "**/*.pb",
        "**/*.dcp",
        "**/*.bit",
        "**/*.bin",
        "**/*.hwh",
        "**/*.gen/**",
        # Python & C/C++ Artifacts
        "**/__pycache__/**",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        ".venv/**",
        "venv/**",
        "**/*.egg-info/**",
        "dist/**",
        "build/**",
        "**/*.o",
        "**/*.a",
        "**/*.so",
        "**/*.dylib",
        "**/*.dll",
        # OS Noise
        "**/.DS_Store",
        "**/Thumbs.db",
    ]

    IGNORE_CANDIDATE_PATHS = (
        Path("context") / "conf" / "cog.ignore",
        Path(".cog") / "cog.ignore",
        Path("cog.ignore"),
        Path(".cogignore"),
    )

    def __init__(
        self,
        repo_root: Path,
        custom_ignore_path: Optional[Path] = None,
        use_gitignore: bool = True,
    ):
        self.repo_root = repo_root.resolve()
        self.raw_patterns: List[str] = list(self.DEFAULT_IGNORE_PATTERNS)
        self.compiled_rules: List[Tuple[re.Pattern, bool]] = []  # (regex, is_negation)

        # 1. Automatically parse .gitmodules to exclude all submodule paths
        self._load_gitmodules_rules()

        # 2. Load .gitignore if present
        if use_gitignore:
            gitignore_file = self.repo_root / ".gitignore"
            if gitignore_file.is_file():
                self._load_file_rules(gitignore_file)

        # 3. Resolve and load cog.ignore
        ignore_file = self._resolve_ignore_path(custom_ignore_path)
        if ignore_file and ignore_file.is_file():
            self._load_file_rules(ignore_file)

        # 4. Compile all patterns to regex
        self._compile_patterns()

    def _load_gitmodules_rules(self):
        """Auto-detects and ignores all submodules declared in .gitmodules."""
        gitmodules_file = self.repo_root / ".gitmodules"
        if not gitmodules_file.is_file():
            return

        try:
            with open(gitmodules_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Find all path = <submodule_path> entries
            submodule_paths = re.findall(r"^\s*path\s*=\s*(.+)$", content, re.MULTILINE)
            for sub_path in submodule_paths:
                clean_path = sub_path.strip().strip("'\"")
                if clean_path:
                    self.raw_patterns.append(clean_path)
                    self.raw_patterns.append(f"{clean_path}/**")
        except Exception:
            pass

    def _resolve_ignore_path(self, custom_path: Optional[Path] = None) -> Optional[Path]:
        """Resolves the location of the cog.ignore file."""
        if custom_path:
            p = Path(custom_path)
            return p.resolve() if p.is_absolute() else (self.repo_root / p).resolve()

        for candidate in self.IGNORE_CANDIDATE_PATHS:
            candidate_full = self.repo_root / candidate
            if candidate_full.is_file():
                return candidate_full

        return None

    def _load_file_rules(self, filepath: Path):
        """Reads patterns from a file, ignoring comments and blank lines."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    self.raw_patterns.append(line)
        except Exception:
            pass

    @staticmethod
    def _rule_to_regex(pattern: str) -> Tuple[Optional[re.Pattern], bool]:
        """Translates a Git-style glob pattern into a compiled regex."""
        is_negation = pattern.startswith("!")
        if is_negation:
            pattern = pattern[1:].strip()

        if not pattern:
            return None, False

        # Normalize slashes
        pattern = pattern.replace("\\", "/")

        # Match directories specifically
        is_dir_only = pattern.endswith("/")
        if is_dir_only:
            pattern = pattern[:-1]

        # Handle leading slash (relative to root) vs anywhere in path
        if pattern.startswith("/"):
            pattern = pattern[1:]
            regex_str = "^"
        elif "/" in pattern:
            regex_str = "^"
        else:
            # Pattern can match in any subdirectory
            regex_str = "(^|/)"

        # Escape special regex characters except * and ?
        i = 0
        n = len(pattern)
        res = []

        while i < n:
            c = pattern[i]
            if c == "*":
                if i + 1 < n and pattern[i + 1] == "*":
                    # Double star '**'
                    if i + 2 < n and pattern[i + 2] == "/":
                        res.append("(?:.+/)?")
                        i += 3
                        continue
                    else:
                        res.append(".*")
                        i += 2
                        continue
                else:
                    # Single star '*' (matches within directory component)
                    res.append("[^/]*")
            elif c == "?":
                res.append("[^/]")
            elif c in r"\.+^$(){}|[]":
                res.append("\\" + c)
            else:
                res.append(c)
            i += 1

        regex_str += "".join(res)
        if is_dir_only:
            regex_str += "(/.*)?$"
        else:
            regex_str += "($|/.*$)"

        try:
            return re.compile(regex_str), is_negation
        except re.error:
            return None, False

    def _compile_patterns(self):
        """Compiles all raw patterns into regex rules."""
        self.compiled_rules = []
        for pat in self.raw_patterns:
            compiled, is_negation = self._rule_to_regex(pat)
            if compiled:
                self.compiled_rules.append((compiled, is_negation))

    def is_ignored(self, path: Path) -> bool:
        """
        Determines whether a given path (relative to repo_root or absolute) is ignored.
        """
        if path.is_absolute():
            try:
                rel_path = path.resolve().relative_to(self.repo_root)
            except ValueError:
                return False
        else:
            rel_path = path

        posix_str = rel_path.as_posix()
        ignored = False

        for regex, is_negation in self.compiled_rules:
            if regex.search(posix_str):
                ignored = not is_negation

        return ignored