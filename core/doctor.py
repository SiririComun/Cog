#!/usr/bin/env python3
"""
Cog: Repository Diagnostics & Integrity Inspector (doctor.py)
Performs automated pre-flight checks on configuration health, toolchain metadata,
target file paths, Git status, and simulated token budget thresholds.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from bd_pruner import BlockDesignPruner
from code_minifier import CodeMinifier
from git_graph import GitGraphExtractor
from ipynb_clean import NotebookCleaner
from token_meter import TokenMeter
from xdc_clean import XdcCleaner


class DiagnosticDoctor:
    """
    Evaluates repository context health and prints actionable pre-flight diagnostics.
    """

    SINGLE_FILE_TOKEN_WARN_THRESHOLD = 25000
    TOTAL_PAYLOAD_TOKEN_WARN_THRESHOLD = 128000

    def __init__(self, engine):
        self.engine = engine
        self.repo_root = engine.repo_root

    def run_diagnostics(self) -> Dict[str, Any]:
        """Runs full health audit across config, toolchain, files, and token budgets."""
        report: Dict[str, Any] = {
            "config_found": self.engine.config_file.is_file(),
            "config_path": str(self.engine.config_file),
            "valid_targets": [],
            "missing_targets": [],
            "ignored_targets": [],
            "toolchain_meta": {},
            "git_info": {},
            "token_breakdown": {},
            "total_estimated_tokens": 0,
            "total_compacted_bytes": 0,
            "large_files": [],
            "warnings": [],
            "errors": [],
        }

        # 1. Check Configuration File
        if not report["config_found"]:
            report["errors"].append(
                f"Configuration file not found: {self.engine.config_file}"
            )
            return report

        # 2. Parse and Validate Targets
        targets, output_path = self.engine.parse_config()
        report["output_path"] = str(output_path)

        for target_rel in targets:
            target_path = self.repo_root / target_rel
            if not target_path.is_file():
                report["missing_targets"].append(target_rel)
            elif self.engine.ignore_filter.is_ignored(Path(target_rel)):
                report["ignored_targets"].append(target_rel)
            else:
                report["valid_targets"].append(target_rel)

        if report["missing_targets"]:
            report["warnings"].append(
                f"{len(report['missing_targets'])} targets in cog.conf no longer exist on disk."
            )

        # 3. Toolchain & Environment Metadata Audit
        meta = self.engine.extract_toolchain_metadata()
        report["toolchain_meta"] = meta

        # 4. Git Context Audit
        active_branch = (
            GitGraphExtractor._run_git(["branch", "--show-current"], cwd=str(self.repo_root))
            or "HEAD (detached)"
        )
        active_sha = (
            GitGraphExtractor._run_git(["rev-parse", "--short", "HEAD"], cwd=str(self.repo_root))
            or "unknown"
        )
        status_short = GitGraphExtractor._run_git(["status", "--short"], cwd=str(self.repo_root))
        report["git_info"] = {
            "branch": active_branch,
            "sha": active_sha,
            "is_dirty": bool(status_short),
            "dirty_count": len(status_short.splitlines()) if status_short else 0,
        }

        # 5. Dry-Run Token Compaction Audit
        total_tokens = 0
        total_bytes = 0
        breakdown: Dict[str, int] = {}

        for target_rel in report["valid_targets"]:
            target_path = self.repo_root / target_rel
            try:
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()

                ext = target_path.suffix.lower()
                if ext == ".bd":
                    processed = BlockDesignPruner.prune_bd_json(raw_text)
                    cat = "Hardware (BD)"
                elif ext == ".ipynb":
                    processed = NotebookCleaner.clean_notebook(raw_text)
                    cat = "Notebooks"
                elif ext == ".xdc":
                    processed = XdcCleaner.clean_xdc(raw_text)
                    cat = "Constraints"
                elif ext in (".vhd", ".vhdl", ".v", ".sv"):
                    processed = CodeMinifier.minify(raw_text, ext)
                    cat = "Hardware (RTL)"
                else:
                    processed = CodeMinifier.minify(raw_text, ext)
                    cat = "Software / Docs"

                file_tokens = TokenMeter.estimate_tokens(processed)
                total_tokens += file_tokens
                total_bytes += len(processed.encode("utf-8"))

                breakdown[cat] = breakdown.get(cat, 0) + file_tokens

                if file_tokens >= self.SINGLE_FILE_TOKEN_WARN_THRESHOLD:
                    report["large_files"].append((target_rel, file_tokens))
                    report["warnings"].append(
                        f"Large target detected: '{target_rel}' (~{file_tokens:,} tokens)."
                    )
            except Exception as e:
                report["warnings"].append(f"Failed to inspect '{target_rel}': {str(e)}")

        report["token_breakdown"] = breakdown
        report["total_estimated_tokens"] = total_tokens
        report["total_compacted_bytes"] = total_bytes

        if total_tokens >= self.TOTAL_PAYLOAD_TOKEN_WARN_THRESHOLD:
            report["warnings"].append(
                f"Total context payload exceeds ~{self.TOTAL_PAYLOAD_TOKEN_WARN_THRESHOLD:,} tokens "
                f"(projected: ~{total_tokens:,} tokens)."
            )

        return report

    def print_diagnostic_report(self):
        """Formats and prints the diagnostic doctor summary."""
        diag = self.run_diagnostics()

        print("\n" + "=" * 70)
        print("  🩺 COG DOCTOR: REPOSITORY PRE-FLIGHT DIAGNOSTICS")
        print("=" * 70)

        # 1. Configuration Status
        if diag["config_found"]:
            print(f"  • Configuration : ✅ Active ({diag['config_path']})")
        else:
            print(f"  • Configuration : ❌ MISSING ({diag['config_path']})")
            print("    👉 Run './Cog/Ctx init' to generate configuration.")
            print("=" * 70 + "\n")
            return

        print(f"  • Target Destination: {diag.get('output_path', 'default')}")

        # 2. Target File Integrity
        v_count = len(diag["valid_targets"])
        m_count = len(diag["missing_targets"])
        i_count = len(diag["ignored_targets"])
        print(f"  • Targets Audit : {v_count} valid | {m_count} missing | {i_count} ignored")

        if diag["missing_targets"]:
            print("\n  ⚠️  Missing Target References:")
            for m in diag["missing_targets"]:
                print(f"     • ❌ {m}")

        # 3. Toolchain Detection
        print("\n" + "-" * 70)
        print("  ⚙️  Toolchain & Environment Auto-Detection:")
        meta = diag["toolchain_meta"]
        print(f"     • Vivado Version  : {meta.get('vivado_version') or '⚠️ (Not detected)'}")
        print(f"     • Target Part     : {meta.get('target_part') or '⚠️ (Not detected)'}")
        print(f"     • HDL Language    : {meta.get('target_language') or '⚠️ (Not detected)'}")
        print(f"     • Pinned Overlay  : {meta.get('hardware_pinning') or '⚠️ (Not detected)'}")
        print(f"     • Package Version : {('v' + meta['package_version']) if meta.get('package_version') else '⚠️ (Not detected)'}")

        # 4. Git Status
        print("\n" + "-" * 70)
        print("  🌳 Git Repository Health:")
        git = diag["git_info"]
        git_clean_str = "✅ Clean" if not git["is_dirty"] else f"⚠️ Dirty ({git['dirty_count']} uncommitted files)"
        print(f"     • Active Branch   : {git['branch']} @ {git['sha']}")
        print(f"     • Working Tree    : {git_clean_str}")

        # 5. Projected Token Footprint
        print("\n" + "-" * 70)
        print("  📊 Projected LLM Context Footprint (Dry-Run Compaction):")
        print(f"     • Total Payload   : {diag['total_compacted_bytes'] / 1024:.1f} KB")
        print(f"     • Estimated Tokens: ~{diag['total_estimated_tokens']:,} tokens")

        if diag["token_breakdown"]:
            print("\n     📂 Token Distribution by Domain:")
            for cat, tokens in diag["token_breakdown"].items():
                print(f"        • {cat:<18}: ~{tokens:,} tokens")

        if diag["large_files"]:
            print("\n     ⚠️  High-Footprint Individual Files (>25k tokens):")
            for fname, ftok in diag["large_files"]:
                print(f"        • {fname} (~{ftok:,} tokens)")

        # 6. Overall Verdict
        print("\n" + "=" * 70)
        if not diag["errors"] and not diag["warnings"]:
            print("  🎉 HEALTH VERDICT: EXCELLENT (All checks passed with 0 warnings)")
        elif not diag["errors"]:
            print(f"  ⚠️  HEALTH VERDICT: PASSED WITH {len(diag['warnings'])} WARNINGS")
        else:
            print(f"  ❌ HEALTH VERDICT: FAILED WITH {len(diag['errors'])} ERRORS")
        print("=" * 70 + "\n")