#!/usr/bin/env python3
"""
Cog: Git Topology Extractor (git_graph.py)
Extracts active branch status, tracking divergence, release tags, and
multi-branch commit graphs in both token-compact and full topology modes.
"""

import subprocess
from typing import List, Optional


class GitGraphExtractor:
    """
    Extracts multi-branch commit topology, branch tracking, tags, and dirty state.
    Supports 'compact' (15 commits, top 5 tags) and 'full' (complete history) modes.
    """

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
    def extract_summary(
        cls,
        repo_root: str = ".",
        mode: str = "compact",
        max_commits: Optional[int] = None,
    ) -> str:
        """
        Extracts Git repository topology summary.
        - mode='compact': 15 commits, top 5 tags, concise status.
        - mode='full'   : Uncapped commit graph, complete tag history, detailed dirty file list.
        """
        is_full = (mode.lower() == "full")
        commit_limit = max_commits if max_commits is not None else (None if is_full else 15)
        tag_limit = None if is_full else 5

        sections = []

        # 1. Active Branch & Working Tree Status
        curr_branch = (
            cls._run_git(["branch", "--show-current"], cwd=repo_root)
            or "HEAD (detached)"
        )
        status_short = cls._run_git(["status", "--short"], cwd=repo_root)

        if not status_short:
            clean_state = "Clean (No uncommitted changes)"
        else:
            dirty_lines = status_short.splitlines()
            clean_state = f"Dirty ({len(dirty_lines)} modified/untracked files)"

        sections.append(f"Current Branch: {curr_branch} | Working Tree: {clean_state}")

        # If in full mode and working tree is dirty, append file status list
        if is_full and status_short:
            sections.append("\nWorking Tree Changes:\n" + status_short)

        # 2. Branch Tracking & Divergence Status
        branch_vv = cls._run_git(["branch", "-a", "-vv"], cwd=repo_root)
        if branch_vv:
            sections.append("\nBranch Tracking & Divergence Status:\n" + branch_vv)

        # 3. Tags & Releases
        tags = cls._run_git(["tag", "-n1", "--sort=-creatordate"], cwd=repo_root)
        if tags:
            tag_lines = tags.splitlines()
            if tag_limit:
                tag_lines = tag_lines[:tag_limit]
            sections.append("\nRepository Tags & Release History:\n" + "\n".join(tag_lines))

        # 4. Multi-Branch Commit Graph
        log_args = [
            "log",
            "--all",
            "--graph",
            "--pretty=format:%h %d - %cd : %s (%an)",
            "--date=short",
        ]
        if commit_limit:
            log_args.extend(["-n", str(commit_limit)])

        graph = cls._run_git(log_args, cwd=repo_root)
        if graph:
            sections.append("\nMulti-Branch Git Commit Graph:\n" + graph)

        return "\n".join(sections)