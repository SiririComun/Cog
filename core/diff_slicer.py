#!/usr/bin/env python3
"""
Cog: Working Tree Diff Slicer (diff_slicer.py)
Extracts unified git diffs alongside compacted context for modified files,
optimized for pre-commit AI code reviews and commit message drafting.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from bd_pruner import BlockDesignPruner
from c_slicer import CSlicer
from code_minifier import CodeMinifier
from git_graph import GitGraphExtractor
from ipynb_clean import NotebookCleaner
from tcl_clean import TclCleaner
from xdc_clean import XdcCleaner


class DiffSlicer:
    """
    Extracts working tree changes (staged and unstaged) and pairs the unified diff
    with domain-compacted full-file representations of the modified targets.
    """

    @staticmethod
    def _run_git(args: List[str], cwd: str = ".") -> str:
        """Runs git command safely and returns standard output."""
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            return res.stdout.strip()
        except Exception:
            return ""

    @classmethod
    def get_modified_files(cls, repo_root: Path, ignore_filter) -> List[str]:
        """
        Returns relative paths of all modified, staged, or untracked files,
        filtered against ignore rules.
        """
        status_output = cls._run_git(["status", "--porcelain"], cwd=str(repo_root))
        if not status_output:
            return []

        modified: List[str] = []
        for line in status_output.splitlines():
            if len(line) < 3:
                continue

            # Format: XY <file_path> or XY <old_path> -> <new_path>
            raw_path = line[3:].strip()
            if "->" in raw_path:
                raw_path = raw_path.split("->", 1)[1].strip()

            rel_path = Path(raw_path)
            full_path = repo_root / rel_path

            if full_path.is_file() and not ignore_filter.is_ignored(rel_path):
                modified.append(rel_path.as_posix())

        return list(dict.fromkeys(modified))

    @classmethod
    def generate_diff_context(cls, engine) -> Tuple[str, int]:
        """
        Generates diff context payload:
        1. Toolchain Banner & Active Git Snapshot
        2. Unified Git Diff Patch
        3. Compacted content of all modified files
        """
        repo_root = engine.repo_root
        ignore_filter = engine.ignore_filter
        modified_files = cls.get_modified_files(repo_root, ignore_filter)

        buffer: List[str] = []
        raw_total_bytes = 0

        # 1. Toolchain & Git Banner
        toolchain_meta = engine.extract_toolchain_metadata()
        active_branch = (
            cls._run_git(["branch", "--show-current"], cwd=str(repo_root))
            or "HEAD (detached)"
        )
        active_sha = (
            cls._run_git(["rev-parse", "--short", "HEAD"], cwd=str(repo_root))
            or "unknown"
        )
        buffer.append(
            engine.format_environment_banner(
                toolchain_meta, git_branch=active_branch, git_sha=active_sha
            )
        )

        # 2. Status & Unified Diff Block
        diff_patch = cls._run_git(["diff", "HEAD"], cwd=str(repo_root))
        # Fallback if no commits exist yet or HEAD unresolvable
        if not diff_patch:
            diff_patch = cls._run_git(["diff"], cwd=str(repo_root))

        buffer.append("Git Working Tree Diff Summary:\n")
        buffer.append("```log")
        buffer.append(f"Active Branch: {active_branch} @ {active_sha}")
        buffer.append(f"Modified Files ({len(modified_files)} files):")
        for mf in modified_files:
            buffer.append(f"  • {mf}")
        buffer.append("```\n")

        if diff_patch:
            raw_total_bytes += len(diff_patch.encode("utf-8"))
            buffer.append("Unified Working Tree Diff Patch (HEAD vs Working Tree):\n")
            buffer.append("```diff")
            buffer.append(diff_patch)
            buffer.append("```\n")
        else:
            buffer.append("```text\n✅ Working tree is clean (no uncommitted diffs detected).\n```\n")

        # 3. Compacted Full-File Content for Modified Files
        if modified_files:
            buffer.append("Full Context for Modified Files (Domain-Compacted):\n")

            for target_rel in modified_files:
                target_path = repo_root / target_rel
                if not target_path.is_file():
                    continue

                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()

                raw_total_bytes += len(raw_text.encode("utf-8"))
                ext = target_path.suffix.lower()
                syntax = engine.SYNTAX_MAP.get(ext, "text")

                if ext == ".bd":
                    processed_text = BlockDesignPruner.prune_bd_json(raw_text)
                elif ext == ".ipynb":
                    processed_text = NotebookCleaner.clean_notebook(raw_text)
                elif ext == ".xdc":
                    processed_text = XdcCleaner.clean_xdc(raw_text)
                elif ext == ".tcl":
                    processed_text = TclCleaner.clean_tcl(raw_text)
                elif ext in (".c", ".cpp", ".h", ".hpp"):
                    processed_text = CSlicer.slice_c_cpp(raw_text, ext)
                else:
                    processed_text = CodeMinifier.minify(raw_text, ext)

                buffer.append(f"{target_path.name}: ({target_rel})\n")
                buffer.append(f"```{syntax}")
                buffer.append(processed_text)
                buffer.append("```\n")

        final_output = "\n".join(buffer)
        return final_output, raw_total_bytes