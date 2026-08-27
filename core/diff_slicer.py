#!/usr/bin/env python3
"""
Cog: Git Diff & Pull Request Slicer (diff_slicer.py)
Extracts working-tree diffs and branch PR diffs alongside domain-compacted context
for modified files, optimized for AI code reviews and automated PR descriptions.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

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
    Extracts working tree changes and feature branch PR deltas, pairing unified diffs
    with domain-compacted representations of modified targets.
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
    def resolve_base_branch(cls, repo_root: Path, target_base: Optional[str] = None) -> str:
        """Resolves target base branch with fallbacks for main/master/remotes."""
        if target_base:
            # Check if provided branch exists
            if cls._run_git(["rev-parse", "--verify", target_base], cwd=str(repo_root)):
                return target_base
            if cls._run_git(["rev-parse", "--verify", f"origin/{target_base}"], cwd=str(repo_root)):
                return f"origin/{target_base}"

        # Standard candidate fallbacks
        for candidate in ("main", "origin/main", "master", "origin/master"):
            if cls._run_git(["rev-parse", "--verify", candidate], cwd=str(repo_root)):
                return candidate

        return "HEAD~1"

    @classmethod
    def get_modified_files(cls, repo_root: Path, ignore_filter) -> List[str]:
        """Returns relative paths of all modified, staged, or untracked files."""
        status_output = cls._run_git(["status", "--porcelain"], cwd=str(repo_root))
        if not status_output:
            return []

        modified: List[str] = []
        for line in status_output.splitlines():
            if len(line) < 3:
                continue

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
        """Generates working tree diff context payload."""
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

    @classmethod
    def generate_pr_context(cls, engine, target_base: Optional[str] = None) -> Tuple[str, int, str]:
        """
        Generates comprehensive Pull Request (PR) review context:
        - Commits touched in branch (base...HEAD)
        - Full triple-dot branch diff
        - Compacted representation of all modified files
        """
        repo_root = engine.repo_root
        base_branch = cls.resolve_base_branch(repo_root, target_base)

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

        # 2. Branch Commits & Diff Scope
        commits_log = cls._run_git(
            ["log", f"{base_branch}..HEAD", "--pretty=format:* %h - %cd : %s (%an)", "--date=short"],
            cwd=str(repo_root),
        )
        changed_files_raw = cls._run_git(
            ["diff", "--name-only", f"{base_branch}...HEAD"], cwd=str(repo_root)
        )

        changed_files: List[str] = []
        for line in changed_files_raw.splitlines():
            line = line.strip()
            if line and (repo_root / line).is_file() and not engine.ignore_filter.is_ignored(Path(line)):
                changed_files.append(line)

        buffer.append(f"Pull Request Review Scope ({base_branch} ← {active_branch}):\n")
        buffer.append("```log")
        buffer.append(f"Base Branch   : {base_branch}")
        buffer.append(f"Feature Branch: {active_branch} @ {active_sha}")
        buffer.append(f"\nCommits in this PR:")
        buffer.append(commits_log if commits_log else "  • (No commit divergence from base branch)")
        buffer.append(f"\nFiles Modified in this PR ({len(changed_files)} files):")
        for cf in changed_files:
            buffer.append(f"  • {cf}")
        buffer.append("```\n")

        # 3. Full Triple-Dot Branch Diff Patch
        pr_diff = cls._run_git(["diff", f"{base_branch}...HEAD"], cwd=str(repo_root))
        if pr_diff:
            raw_total_bytes += len(pr_diff.encode("utf-8"))
            buffer.append(f"Unified Branch Diff Patch ({base_branch}...{active_branch}):\n")
            buffer.append("```diff")
            buffer.append(pr_diff)
            buffer.append("```\n")
        else:
            buffer.append("```text\n✅ No diff detected between feature branch and base branch.\n```\n")

        # 4. Compacted Content for All PR Modified Files
        if changed_files:
            buffer.append("Full Context for PR Modified Files (Domain-Compacted):\n")
            for target_rel in changed_files:
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
        return final_output, raw_total_bytes, base_branch