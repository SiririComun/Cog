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
from scaffold import ConfigScaffolder
from doctor import DiagnosticDoctor
from xdc_clean import XdcCleaner
from tcl_clean import TclCleaner
from c_slicer import CSlicer
from diff_slicer import DiffSlicer

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
        Parses the resolved cog.conf for target files, expanding glob patterns
        (e.g., core/*.py, src/**/*.vhd), filtering through IgnoreFilter,
        and deduplicating while preserving insertion order.
        """
        raw_targets: List[str] = []
        output_file = self.repo_root / "context" / "summary.txt"

        if not self.config_file.is_file():
            return [], output_file

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
                    raw_targets.append(line)

        resolved_targets: List[str] = []

        for target_entry in raw_targets:
            # Clean leading slashes / relative notation
            clean_entry = target_entry.lstrip("./\\")

            # Check if entry contains wildcard / glob characters
            has_glob = any(char in clean_entry for char in ("*", "?", "["))

            if has_glob:
                matched_files: List[Path] = []
                try:
                    for matched_path in self.repo_root.glob(clean_entry):
                        if matched_path.is_file():
                            rel = matched_path.relative_to(self.repo_root)
                            if not self.ignore_filter.is_ignored(rel):
                                matched_files.append(rel)
                except Exception:
                    pass

                # Sort matches deterministically
                matched_files.sort(key=lambda p: p.as_posix())
                for rel_p in matched_files:
                    resolved_targets.append(rel_p.as_posix())

            else:
                target_path = self.repo_root / clean_entry
                if target_path.is_file():
                    rel = target_path.relative_to(self.repo_root)
                    if not self.ignore_filter.is_ignored(rel):
                        resolved_targets.append(rel.as_posix())

        # Deduplicate while preserving group insertion order
        unique_targets = list(dict.fromkeys(resolved_targets))
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

            # Apply domain-specific compaction inside the loop
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

        # Write distilled payload to destination file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output)

        TokenMeter.print_report(raw_total_bytes, final_output, str(output_file))

    def handle_init(self, args: List[str]):
        """Executes the automated repository onboarding & configuration scaffolding."""
        force = any(flag in args for flag in ("--force", "-f"))
        scaffolder = ConfigScaffolder(self.repo_root)
        success, conf_path, ignore_path, scan_results = scaffolder.scaffold(force=force)

        if not success:
            print("\n⚠️  [Cog WARNING] Configuration already exists:")
            print(f"   • {conf_path}")
            print("\nUse './Cog/Ctx init --force' to overwrite existing configuration.\n")
            return

        total_files = sum(len(f) for f in scan_results.values())

        print("\n" + "=" * 68)
        print("  🎉 COG PROJECT INITIALIZATION COMPLETE")
        print("=" * 68)
        print(f"  • Configuration     : {conf_path}")
        print(f"  • Ignore Rules      : {ignore_path}")
        print(f"  • Total Discovered  : {total_files} files classified across domains")
        print("=" * 68)

        for domain, files in scan_results.items():
            if files:
                print(f"  📂 [{domain.upper()}]: {len(files)} files")

        print("=" * 68)
        print("  👉 Next Step: Review your 'context/conf/cog.conf' and run:")
        print("     ./Cog/Ctx")
        print("=" * 68 + "\n")

    def handle_update(self, args: List[str]):
        """Non-destructively synchronizes existing configuration with new repository files."""
        scaffolder = ConfigScaffolder(self.repo_root)
        success, conf_path, newly_added, missing = scaffolder.update(self.config_file)

        if not success:
            print("\n❌ [Cog ERROR] No configuration file found to update.")
            print("   Run './Cog/Ctx init' first to generate your initial configuration.\n")
            return

        print("\n" + "=" * 68)
        print("  🔄 COG CONFIGURATION SYNC COMPLETE")
        print("=" * 68)
        print(f"  • Configuration : {conf_path}")
        print(f"  • Newly Added   : {len(newly_added)} new files appended")
        if missing:
            print(f"  • Missing / Moved: {len(missing)} files flagged")
        print("=" * 68)

        if newly_added:
            print("  ➕ Newly Added Files:")
            for f in newly_added:
                print(f"     • {f}")
            print("=" * 68)

        if missing:
            print("  ⚠️  Flagged Missing Targets (declared in config but missing on disk):")
            for f in missing:
                print(f"     • {f}")
            print("=" * 68)

        if not newly_added and not missing:
            print("  ✅ All files are up to date. No configuration changes required.")
            print("=" * 68)

        print("  👉 Ready to generate context: run './Cog/Ctx'\n")
    
    def handle_check(self, args: List[str]):
        """Executes repository diagnostics and token health checks."""
        doctor = DiagnosticDoctor(self)
        doctor.print_diagnostic_report()

    def handle_git(self, mode: str = "compact", args: Optional[List[str]] = None):
        """Generates a standalone Git topology context payload."""
        args = args or []
        output_file = self.repo_root / "context" / f"git_{mode}_summary.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        buffer: List[str] = []
        raw_total_bytes = 0

        # 1. Environment Banner
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

        # 2. Multi-Branch Git Topology
        git_summary = GitGraphExtractor.extract_summary(
            str(self.repo_root), mode=mode
        )
        raw_total_bytes = len(git_summary.encode("utf-8"))

        buffer.append("Git Context & Branch Topology:\n")
        buffer.append("```log")
        buffer.append(git_summary)
        buffer.append("```\n")

        final_output = "\n".join(buffer)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output)

        TokenMeter.print_report(raw_total_bytes, final_output, str(output_file))

    def handle_diff(self, args: Optional[List[str]] = None):
        """Generates a working-tree diff and modified files context payload."""
        output_file = self.repo_root / "context" / "diff_summary.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        final_output, raw_bytes = DiffSlicer.generate_diff_context(self)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output)

        TokenMeter.print_report(raw_bytes, final_output, str(output_file))

    def handle_pr(self, args: Optional[List[str]] = None):
        """Generates a Pull Request review context comparing feature branch against base."""
        args = args or []
        base_branch_arg = args[0] if args else None

        output_file = self.repo_root / "context" / "pr_review_summary.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        final_output, raw_bytes, resolved_base = DiffSlicer.generate_pr_context(
            self, target_base=base_branch_arg
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output)

        print(f"  • Base Branch       : {resolved_base}")
        TokenMeter.print_report(raw_bytes, final_output, str(output_file))

    def dispatch(self, args: list):
        """CLI Command & Option Dispatcher."""
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

        subcommand = filtered_args[0].lower() if filtered_args else "full"

        if subcommand in ("init", "setup"):
            self.handle_init(filtered_args[1:])
        elif subcommand in ("update", "sync"):
            self.handle_update(filtered_args[1:])
        elif subcommand in ("check", "doctor"):
            self.handle_check(filtered_args[1:])
        elif subcommand in ("git", "git:compact", "git_compact"):
            self.handle_git(mode="compact", args=filtered_args[1:])
        elif subcommand in ("git:full", "git_full", "git:all"):
            self.handle_git(mode="full", args=filtered_args[1:])
        elif subcommand in ("diff", "changes", "staged"):
            self.handle_diff(filtered_args[1:])
        elif subcommand in ("pr", "review"):
            self.handle_pr(filtered_args[1:])
        elif subcommand in ("full", "all"):
            self.generate_full_context()
        else:
            self.generate_full_context()

if __name__ == "__main__":
    target_repo = Path.cwd()
    engine = CogEngine(target_repo)
    engine.dispatch(sys.argv[1:])