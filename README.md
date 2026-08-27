# 🧠 Cog — Context on Git

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Standard%20Library)-brightgreen.svg)]()
[![Platforms](https://img.shields.io/badge/Platforms-Linux%20%7C%20macOS%20%7C%20Windows-blue.svg)]()
[![Git Submodule Pattern](https://img.shields.io/badge/Pattern-Git%20Submodule-blueviolet.svg)]()
[![Release](https://img.shields.io/badge/Release-v0.1.0-orange.svg)](https://github.com/SiririComun/Cog/releases)

> **High-density, token-optimized codebase context distillation for LLMs and AI-assisted engineering.**

Inspired by [CERN's Hog (HDL on Git)](https://cern.ch/hog), **Cog** is a lightweight, zero-dependency Git utility designed to extract, prune, and format complex multi-branch hardware (FPGA/ASIC), software (Python/C++), and Jupyter Notebook repositories into a single compact context document optimized for Large Language Models (GPT-4, Claude, Gemini).

---

```
   ___  ___   __ _
  / __|/ _ \ / _` |
 | (__| (_) | (_| |
  \___|\___/ \__, |
             |___/
 Context on Git Engine
```

---

## 🌟 Key Features

* 🚀 **Zero External Dependencies:** Built entirely with POSIX Bash, Windows Batch/PowerShell, and the Python standard library. Runs out of the box on Linux, macOS, Windows (`cmd.exe`/PowerShell), CI runners, and embedded Linux boards (PYNQ/Raspberry Pi) without `pip install`.
* ⚙️ **Automatic Toolchain & Environment Lock:** Auto-detects Vivado versions from `hog.conf` / `.bd`, target FPGA parts (`xc7z020...`), primary HDL languages, pinned overlay versions (`hardware.json`), and active Git commit SHAs. Anchors this metadata at the very first line of the prompt to eliminate toolchain hallucinations.
* 📉 **Surgical Hardware & Data Compaction (Zero Semantic Loss):**
  * **Deep Vivado Block Design Pruner (`.bd`):** Recursively purges massive Xilinx `LAYERED_METADATA` struct dumps, collapses redundant DDR/Fixed-IO pinout arrays, strips SmartConnect parameter repetition, and removes default Zynq/MicroBlaze MIO boilerplate while preserving **100% of custom IP blocks, AXI interconnects, and physical memory maps (`SEG_*` offsets and ranges)**.
  * **Jupyter Notebook Distiller (`.ipynb`):** Strips output blobs, base64 image strings, and execution counters. Preserves 100% of executable Python code cells, hardware pinout tables, and section headers with **safety-critical keyword protection** (never truncating voltage or pin limits).
  * **Vivado Constraint Compactor (`.xdc`):** Consolidates split property lines into native Vivado `-dict { PACKAGE_PIN ... IOSTANDARD ... }` syntax and purges inactive commented pinout bloat.
  * **Vivado & Hog TCL Cleaner (`.tcl`):** Strips auto-generated tool session logs, process IDs, timestamps, and disclaimer comments while leaving build recipes 100% intact.
  * **Embedded C/C++ Driver Slicer (`.c`, `.h`):** Strips multi-line licensing boilerplate while preserving 100% of memory-mapped register `#define` offsets, HLS `#pragma` directives, and bitmask structs.
* 🎯 **Modular Domain Slicing:** Generate targeted slices (`bd`, `rtl`, `sw`, `nb`, `xdc`, `tcl`, `hld`, `app`) to avoid polluting the prompt with irrelevant files.
* 🔍 **Pre-Commit Diffs & PR Review Generator:** Extract working-tree diffs (`./Cog/Ctx diff`) and feature branch pull request scopes (`./Cog/Ctx pr [base_branch]`) with full file grounding for automated AI code reviews.
* 📋 **Clipboard & Stdout Ergonomics:** Direct clipboard injection (`-c` / `--clip`) and Unix stdout piping (`-s` / `--stdout`).
* 📊 **Syntax-Calibrated Token Meter:** Employs a calibrated `~3.62 chars/token` heuristic to report token footprints and dynamic LLM context window compatibility tiers (Universal, Standard, Extended).

---

## 🏛 CLI Command Reference

### 1. Setup & Maintenance
| Command | Alias | Description |
| :--- | :--- | :--- |
| `./Cog/Ctx init` | `setup` | Auto-scaffolds `context/conf/cog.conf` and `context/conf/cog.ignore`. Use `--force` to overwrite. |
| `./Cog/Ctx update` | `sync` | Non-destructively syncs newly discovered files without altering custom comments. |
| `./Cog/Ctx check` | `doctor` | Pre-flight diagnostics: audits target paths, toolchain detection, and token budget. |

### 2. Targeted Domain Slices (Modular Context)
| Command | Alias | What It Slices | Ideal LLM Use Case |
| :--- | :--- | :--- | :--- |
| `./Cog/Ctx bd` | `ip` | Vivado Block Designs (`.bd`) + Address Maps | Debugging AXI address conflicts and IP routing |
| `./Cog/Ctx rtl` | `hw`, `vhd`, `v` | VHDL, Verilog, SystemVerilog cores | Debugging FSM state logic, DSP, and pipelining |
| `./Cog/Ctx sw` | `py`, `driver` | Python drivers, C/C++ headers & bindings | Software API refactoring and register read/writes |
| `./Cog/Ctx nb` | `ipynb` | Distilled Jupyter Notebook tutorials | Troubleshooting tutorial workflows and data plots |
| `./Cog/Ctx docs` | - | Markdown docs, `README.md`, `LICENSE` | Documentation generation and architectural review |
| `./Cog/Ctx xdc` | `pins`, `constraints` | Compacted `.xdc` constraint files | Timing closure and physical pin assignments |
| `./Cog/Ctx tcl` | `build` | Hog & Vivado build scripts | Headless batch runs and CI script debugging |
| `./Cog/Ctx hld` | - | **`bd` + `rtl` + `sw`** | Hardware-Software Co-Design verification |
| `./Cog/Ctx app` | - | **`sw` + `nb`** | Application layer & tutorial debugging |

### 3. Git & Code Review Commands
| Command | Alias | Description |
| :--- | :--- | :--- |
| `./Cog/Ctx git` | `git:compact` | 15-commit multi-branch graph, divergence table, and tags. |
| `./Cog/Ctx git:full` | `git:all` | Complete commit history graph across all branches. |
| `./Cog/Ctx diff` | `staged` | Working tree diff patch + compacted modified files. |
| `./Cog/Ctx pr [base]` | `review` | Branch pull request review scope comparing feature branch against base (default: `main`). |

---

## ⚡ Modifier Flags

Any command supports the following modifier flags:

* **`-c`, `--clip`:** Copies the final context payload directly to your system clipboard (`wl-copy`, `xclip`, `pbcopy`, `clip.exe`).
* **`-s`, `--stdout`:** Streams the raw context payload to `stdout` for Unix piping (e.g. `./Cog/Ctx diff -s | llm "review this"`).
* **`-o <path>`, `--out <path>`:** Overrides the output destination file path.
* **`--no-banner`:** Suppresses the toolchain environment header.
* **`--no-git`:** Suppresses the Git topology section.
* **`--config <path>`:** Overrides configuration file path.

---

## 🚀 Quick Start Guide

### 1. Add `Cog` as a Submodule
```bash
git submodule add https://github.com/SiririComun/Cog.git Cog
git submodule update --init --recursive
```

### 2. Initialize Configuration
```bash
./Cog/Ctx init
```
*(On Windows Command Prompt: `.\Cog\Ctx.cmd init` or PowerShell: `.\Cog\Ctx.ps1 init`)*

### 3. Generate Context
```bash
./Cog/Ctx
```

---

## 🧪 Automated Test Suite

Run the zero-dependency test suite:
```bash
python3 -m unittest discover -s tests -v
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Developed by [SiririComun](https://github.com/SiririComun).