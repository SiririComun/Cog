import subprocess
from typing import Dict


class GitGraphExtractor:
    """Extracts multi-branch commit topology, branch tracking, tags, and dirty state."""

    @staticmethod
    def _run_git(args: list, cwd: str = ".") -> str:
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return res.stdout.strip()
        except Exception:
            return ""

    @classmethod
    def extract_summary(cls, repo_root: str = ".") -> str:
        sections = []

        # 1. Active Branch & Working Tree Status
        curr_branch = cls._run_git(["branch", "--show-current"], cwd=repo_root) or "HEAD (detached)"
        status_short = cls._run_git(["status", "--short"], cwd=repo_root)
        clean_state = "Clean (No uncommitted changes)" if not status_short else f"Dirty ({len(status_short.splitlines())} modified files)"

        sections.append(f"Current Branch: {curr_branch} | Working Tree: {clean_state}")

        # 2. Branch Divergence & Tracking Table
        branch_vv = cls._run_git(["branch", "-a", "-vv"], cwd=repo_root)
        if branch_vv:
            sections.append("\nBranch Tracking & Divergence Status:\n" + branch_vv)

        # 3. Tags & Releases
        tags = cls._run_git(["tag", "-n1", "--sort=-creatordate"], cwd=repo_root)
        if tags:
            sections.append("\nRepository Tags & Release History:\n" + tags)

        # 4. Multi-Branch Commit Graph
        graph = cls._run_git([
            "log", "--all", "--graph",
            "--pretty=format:%h %d - %cd : %s (%an)",
            "--date=short", "-n", "35"
        ], cwd=repo_root)

        if graph:
            sections.append("\nMulti-Branch Git Commit Graph:\n" + graph)

        return "\n".join(sections)