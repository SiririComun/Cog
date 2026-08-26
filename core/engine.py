#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add core directory to python path for internal imports
CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from git_graph import GitGraphExtractor
from bd_pruner import BlockDesignPruner
from ipynb_clean import NotebookCleaner
from code_minifier import CodeMinifier
from token_meter import TokenMeter


class CogEngine:
    SYNTAX_MAP = {
        ".vhd": "vhd", ".vhdl": "vhd",
        ".py": "python",
        ".bd": "json",
        ".json": "json",
        ".ipynb": "python",
        ".yml": "yaml", ".yaml": "yaml",
        ".tcl": "tcl",
        ".xdc": "xdc",
        ".conf": "conf",
        ".src": "src",
        ".sh": "bash"
    }

    def __init__(self, target_repo_root: Path):
        self.repo_root = target_repo_root.resolve()
        self.config_file = self.repo_root / "cog.conf"

    def parse_config(self):
        """Parses cog.conf for target files and output destination, deduplicating paths."""
        targets = []
        output_file = self.repo_root / "context" / "summary.txt"

        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("OUTPUT:"):
                        output_file = self.repo_root / line.split(":", 1)[1].strip()
                    else:
                        targets.append(line)

        # Automatically deduplicate targets while preserving insertion order
        unique_targets = list(dict.fromkeys(targets))
        return unique_targets, output_file

    def generate_full_context(self):
        """Default Mode: Generates the complete, token-compacted repository context."""
        targets, output_file = self.parse_config()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        buffer = []
        raw_total_bytes = 0

        # 1. Git Graph & Branch Topology
        buffer.append("Git Context & Branch Topology:\n")
        buffer.append("```log")
        buffer.append(GitGraphExtractor.extract_summary(str(self.repo_root)))
        buffer.append("```\n")

        # 2. File Ingestion & Domain-Specific Compacting
        for target_rel in targets:
            target_path = self.repo_root / target_rel
            if not target_path.exists():
                continue

            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()

            raw_total_bytes += len(raw_text.encode("utf-8"))
            ext = target_path.suffix.lower()
            syntax = self.SYNTAX_MAP.get(ext, "text")

            # Apply domain-specific pruning
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

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output)

        TokenMeter.print_report(raw_total_bytes, final_output, str(output_file))

    def dispatch(self, args: list):
        """Scalable CLI Command Dispatcher."""
        command = args[0].upper() if args else "FULL"

        if command in ("FULL", "ALL"):
            self.generate_full_context()
        else:
            self.generate_full_context()


if __name__ == "__main__":
    target_repo = Path.cwd()
    engine = CogEngine(target_repo)
    engine.dispatch(sys.argv[1:])