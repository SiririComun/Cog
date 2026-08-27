#!/usr/bin/env python3
"""
Cog: Git Topology Extractor (git_graph.py)
Extracts active branch status, tracking divergence, release tags, and compact multi-branch commit graphs.
"""

import subprocess
from typing import List, Optional


class GitGraphExtractor:
    """Extracts multi-branch commit topology, branch tracking, tags, and dirty state."""

    @staticmethod
    def _run_git(args: List[str], cwd: str = ".") -> str:
        """Executes a git command safely and returns standard output."""
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
    def extract_summary(cls, repo_root: str = ".") -> str:
        """
        Extracts a clean, token-efficient summary of the Git repository:
        1. Current branch and working tree dirty status.
        2. Branch tracking and divergence status.
        3. Release tags.
        4. Multi-branch ASCII commit graph (last 15 commits).
        """
        sections = []

        # 1. Active Branch & Working Tree Status
        curr_branch = (
            cls._run_git(["branch", "--show-current"], cwd=repo_root)
            or "HEAD (detached)"
        )
        status_short = cls._run_git(["status", "--short"], cwd=repo_root)
        clean_state = (
            "Clean (No uncommitted changes)"
            if not status_short
            else f"Dirty ({len(status_short.splitlines())} modified files)"
        )

        sections.append(
            f"Current Branch: {curr_branch} | Working Tree: {clean_state}"
        )

        # 2. Branch Divergence & Tracking Table
        branch_vv = cls._run_git(["branch", "-a", "-vv"], cwd=repo_root)
        if branch_vv:
            sections.append("\nBranch Tracking & Divergence Status:\n" + branch_vv)

        # 3. Tags & Releases (Top 10 most recent)
        tags = cls._run_git(
            ["tag", "-n1", "--sort=-creatordate"], cwd=repo_root
        )
        if tags:
            tag_lines = tags.splitlines()[:10]
            sections.append(
                "\nRepository Tags & Release History:\n"
                + "\n".join(tag_lines)
            )

        # 4. Multi-Branch Commit Graph (Capped to 15 commits for token efficiency)
        graph = cls._run_git(
            [
                "log",
                "--all",
                "--graph",
                "--pretty=format:%h %d - %cd : %s (%an)",
                "--date=short",
                "-n",
                "15",
            ],
            cwd=repo_root,
        )

        if graph:
            sections.append("\nMulti-Branch Git Commit Graph:\n" + graph)

        return "\n".join(sections)