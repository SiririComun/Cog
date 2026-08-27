#!/usr/bin/env python3
"""
Cog: Context on Git - Main Engine Orchestrator
Extracts toolchain metadata, branch topology, and token-compacted codebase context.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add core directory to python path for internal imports
CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from bd_pruner import BlockDesignPruner
from code_minifier import CodeMinifier
from git_graph import GitGraphExtractor
from ipynb_clean import NotebookCleaner
from token_meter import TokenMeter
from ignore_matcher import IgnoreFilter


class CogEngine:
    SYNTAX_MAP = {
        ".vhd": "vhd",
        ".vhdl": "vhd",
        ".v": "verilog",
        ".sv": "systemverilog",
        ".py": "python",
        ".bd": "json",
        ".json": "json",
        ".ipynb": "python",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".tcl": "tcl",
        ".xdc": "xdc",
        ".conf": "conf",
        ".src": "src",
        ".sh": "bash",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".md": "markdown",
    }

    # Prioritized lookup candidate locations for cog.conf
    CONFIG_CANDIDATE_PATHS = (
        Path("context") / "conf" / "cog.conf",
        Path(".cog") / "cog.conf",
        Path("cog.conf"),
    )

    def __init__(
        self,
        target_repo_root: Path,
        config_override: Optional[Path] = None,
        ignore_override: Optional[Path] = None,
    ):
        self.repo_root = target_repo_root.resolve()
        self.config_file = self._resolve_config_path(config_override)
        self.ignore_filter = IgnoreFilter(
            repo_root=self.repo_root, custom_ignore_path=ignore_override
        )

    def _resolve_config_path(self, config_override: Optional[Path] = None) -> Path:
        """
        Resolves the configuration file location following priority hierarchy:
        1. CLI override (--config / -C)
        2. context/conf/cog.conf
        3. .cog/cog.conf
        4. ./cog.conf
        If none exist on disk, defaults to context/conf/cog.conf.
        """
        if config_override:
            override_path = Path(config_override)
            return (
                override_path.resolve()
                if override_path.is_absolute()
                else (self.repo_root / override_path).resolve()
            )

        for candidate in self.CONFIG_CANDIDATE_PATHS:
            candidate_full = self.repo_root / candidate
            if candidate_full.is_file():
                return candidate_full

        # Default fallback for new project initialization
        return self.repo_root / "context" / "conf" / "cog.conf"

    def extract_toolchain_metadata(self) -> Dict[str, Optional[str]]:
        """
        Auto-detects Vivado versions, target FPGA parts, HDL languages,
        and hardware release pinning across Hog/Vivado/PYNQ repositories.
        """
        meta: Dict[str, Optional[str]] = {
            "vivado_version": None,
            "target_part": None,
            "target_language": None,
            "hardware_pinning": None,
            "package_version": None,
        }

        # 1. Scan Hog configuration files (Top/**/hog.conf)
        for hog_conf in self.repo_root.glob("Top/**/hog.conf"):
            if hog_conf.exists():
                try:
                    with open(hog_conf, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    v_match = re.search(r"#\s*vivado\s+([\d\.]+)", content, re.IGNORECASE)
                    if v_match and not meta["vivado_version"]:
                        meta["vivado_version"] = v_match.group(1).strip()

                    part_match = re.search(r"^\s*PART\s*=\s*(.+)$", content, re.MULTILINE)
                    if part_match and not meta["target_part"]:
                        meta["target_part"] = part_match.group(1).strip()

                    lang_match = re.search(r"^\s*TARGET_LANGUAGE\s*=\s*(.+)$", content, re.MULTILINE)
                    if lang_match and not meta["target_language"]:
                        meta["target_language"] = lang_match.group(1).strip()
                except Exception:
                    pass

        # 2. Fallback / Cross-verify with Vivado Block Designs (*.bd)
        if not meta["vivado_version"] or not meta["target_part"]:
            for bd_file in self.repo_root.glob("**/*.bd"):
                try:
                    with open(bd_file, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                    design_info = data.get("design", {}).get("design_info", {})

                    if not meta["vivado_version"] and "tool_version" in design_info:
                        meta["vivado_version"] = str(design_info["tool_version"]).strip()

                    if not meta["target_part"] and "device" in design_info:
                        meta["target_part"] = str(design_info["device"]).strip()
                except Exception:
                    pass

        # 3. Check hardware.json for pinned overlay release (PYNQ workflow)
        hw_json = self.repo_root / "hardware.json"
        if hw_json.exists():
            try:
                with open(hw_json, "r", encoding="utf-8") as f:
                    hw_data = json.load(f)
                repo = hw_data.get("repo", "")
                version = hw_data.get("version", "")
                if repo or version:
                    meta["hardware_pinning"] = f"{repo} @ {version}".strip(" @")
            except Exception:
                pass

        # 4. Check setup.py for package version info
        setup_py = self.repo_root / "setup.py"
        if setup_py.exists():
            try:
                with open(setup_py, "r", encoding="utf-8", errors="ignore") as f:
                    setup_content = f.read()
                pkg_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', setup_content)
                if pkg_match:
                    meta["package_version"] = pkg_match.group(1).strip()
            except Exception:
                pass

        return meta

    def format_environment_banner(
        self,
        meta: Dict[str, Optional[str]],
        git_branch: str = "main",
        git_sha: str = "HEAD",
    ) -> str:
        """Builds a top-level metadata banner to anchor the LLM's toolchain and Git context."""
        lines = [
            "=" * 78,
            "⚙️  PROJECT ENVIRONMENT & TOOLCHAIN CONSTRAINTS",
            "=" * 78,
        ]

        lines.append(f"• Repository State    : {git_branch} @ {git_sha}")

        if meta.get("vivado_version"):
            lines.append(
                f"• Vivado Tool Version : {meta['vivado_version']} (STRICT: Target toolchain for TCL/GUI workflows)"
            )

        if meta.get("target_part"):
            lines.append(f"• Target FPGA Device  : {meta['target_part']}")

        if meta.get("target_language"):
            lines.append(f"• Primary HDL Language: {meta['target_language']}")

        if meta.get("hardware_pinning"):
            lines.append(f"• Pinned HW Overlay   : {meta['hardware_pinning']}")

        if meta.get("package_version"):
            lines.append(f"• Package Version     : v{meta['package_version']}")

        lines.append("=" * 78 + "\n")
        return "\n".join(lines)

    def parse_config(self) -> Tuple[List[str], Path]:
        """
        Parses the resolved cog.conf for target files and output destination,
        deduplicating paths while preserving insertion order.
        """
        targets: List[str] = []
        output_file = self.repo_root / "context" / "summary.txt"

        if self.config_file.is_file():
            with open(self.config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("OUTPUT:"):
                        raw_output = line.split(":", 1)[1].strip()
                        out_path = Path(raw_output)
                        output_file = (
                            out_path.resolve()
                            if out_path.is_absolute()
                            else self.repo_root / out_path
                        )
                    else:
                        targets.append(line)

        unique_targets = list(dict.fromkeys(targets))
        return unique_targets, output_file

    def generate_full_context(self):
        """Default Mode: Generates the complete, token-compacted repository context."""
        targets, output_file = self.parse_config()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        buffer: List[str] = []
        raw_total_bytes = 0

        # 1. Environment & Toolchain Constraints Header (with Git Anchor)
        toolchain_meta = self.extract_toolchain_metadata()
        active_branch = (
            GitGraphExtractor._run_git(
                ["branch", "--show-current"], cwd=str(self.repo_root)
            )
            or "HEAD (detached)"
        )
        active_sha = (
            GitGraphExtractor._run_git(
                ["rev-parse", "--short", "HEAD"], cwd=str(self.repo_root)
            )
            or "unknown"
        )
        buffer.append(
            self.format_environment_banner(
                toolchain_meta, git_branch=active_branch, git_sha=active_sha
            )
        )

        # 2. Git Graph & Multi-Branch Topology
        buffer.append("Git Context & Branch Topology:\n")
        buffer.append("```log")
        buffer.append(GitGraphExtractor.extract_summary(str(self.repo_root)))
        buffer.append("```\n")

        # 3. File Ingestion, Ignore Filtering & Domain-Specific Compacting
        for target_rel in targets:
            target_path = self.repo_root / target_rel

            # Ensure file exists on disk
            if not target_path.is_file():
                continue

            # Respect .gitignore, cog.ignore, and built-in EDA noise rules
            if self.ignore_filter.is_ignored(Path(target_rel)):
                continue

            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()

            raw_total_bytes += len(raw_text.encode("utf-8"))
            ext = target_path.suffix.lower()
            syntax = self.SYNTAX_MAP.get(ext, "text")

            # Apply domain-specific compaction
            if ext == ".bd":
                processed_text = BlockDesignPruner.prune_bd_json(raw_text)
            elif ext == ".ipynb":
                processed_text = NotebookCleaner.clean_notebook(raw_text)
            else:
                processed_text = CodeMinifier.minify(raw_text, ext)

            buffer.append(f"{target_path.name}: ({target_rel})\n")
            buffer.append(f"```{syntax}")
            buffer.append(processed_text)
            buffer.append("```\n")

        final_output = "\n".join(buffer)

        # Write distilled payload to destination file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output)

        TokenMeter.print_report(raw_total_bytes, final_output, str(output_file))

    def dispatch(self, args: list):
        """CLI Command & Option Dispatcher."""
        # Process custom config flags (--config <path> or -C <path>)
        filtered_args = []
        custom_config: Optional[Path] = None

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("--config", "-C") and i + 1 < len(args):
                custom_config = Path(args[i + 1])
                i += 2
            elif arg.startswith("--config="):
                custom_config = Path(arg.split("=", 1)[1])
                i += 1
            else:
                filtered_args.append(arg)
                i += 1

        if custom_config:
            self.config_file = self._resolve_config_path(custom_config)

        command = filtered_args[0].upper() if filtered_args else "FULL"

        if command in ("FULL", "ALL"):
            self.generate_full_context()
        else:
            self.generate_full_context()


if __name__ == "__main__":
    target_repo = Path.cwd()
    engine = CogEngine(target_repo)
    engine.dispatch(sys.argv[1:])