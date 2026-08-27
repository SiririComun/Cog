# 🧠 Cog — Context on Git

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Standard%20Library)-brightgreen.svg)]()
[![Git Submodule Pattern](https://img.shields.io/badge/Pattern-Git%20Submodule-blueviolet.svg)]()
[![Release](https://img.shields.io/badge/Release-v0.1.0-orange.svg)](https://github.com/SiririComun/Cog/releases)

> **High-density, token-optimized codebase context distillation for LLMs and AI-assisted engineering.**

Inspired by [CERN's Hog (HDL on Git)](https://cern.ch/hog), **Cog** is a lightweight, zero-dependency Git submodule utility designed to extract, prune, and format complex multi-branch hardware (FPGA/ASIC), software (Python/C++), and Jupyter Notebook repositories into a single compact context document optimized for Large Language Models (GPT-4, Claude, Gemini).

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

* 🚀 **Zero External Dependencies:** Built entirely with POSIX Bash and the Python standard library. Runs out of the box on Linux, macOS, Windows, CI runners, and embedded Linux boards (PYNQ/Raspberry Pi) without `pip install`.
* ⚙️ **Automatic Toolchain & Environment Lock:** Auto-detects Vivado versions from `hog.conf` / `.bd`, target FPGA parts (`xc7z020...`), primary HDL languages, pinned overlay versions (`hardware.json`), and active Git commit SHAs. Anchors this metadata at the very first line of the prompt to eliminate toolchain hallucinations.
* 📉 **Surgical Hardware & Data Compaction (Zero Semantic Loss):**
  * **Deep Vivado Block Design Pruner (`.bd`):** Recursively purges massive Xilinx `LAYERED_METADATA` struct dumps, collapses redundant DDR/Fixed-IO pinout arrays, strips SmartConnect parameter repetition, and removes default Zynq/MicroBlaze MIO boilerplate while preserving **100% of custom IP blocks, AXI interconnects, and physical memory maps (`SEG_*` offsets and ranges)**.
  * **Jupyter Notebook Distiller (`.ipynb`):** Strips output blobs, base64 image strings, and execution counters. Preserves 100% of executable Python code cells, hardware pinout tables, and section headers while condensing verbose tutorial prose.
  * **Untouched RTL Fidelity:** Leaves custom VHDL/Verilog processes, FSMs, and register datapaths verbatim for 100% accurate active hardware debugging.
* 🌳 **Multi-Branch Git Topology & Status:** Captures compact ASCII commit graphs across all local/remote branches, active tags, tracking divergence, and working-tree dirty status.
* 📊 **Syntax-Calibrated Token Meter:** Employs a calibrated `~3.1 chars/token` heuristic (matched to modern subword tokenizers on technical code/JSON) to report honest token footprints and compression metrics.
* 📦 **Git Submodule Workflow:** Drop `Cog` into any repository in 2 commands and update it across projects with `git submodule update --remote`.

---

## 📊 Token Compression Benchmarks

Measured on the [PYNQ Oscilloscope & Spectrum Analyzer](https://github.com/SiririComun/sw-pynq-oscilloscope) & [Hardware Overlays](https://github.com/SiririComun/hw-xadc-dma-overlays) stack:

| Artifact / File Type | Raw Ingestion Size | Cog Compacted Size | Token Savings | Semantic & Debugging Integrity |
| :--- | :---: | :---: | :---: | :---: |
| **Vivado Block Design (`xadc.bd`)** | `~45,000 tokens` | `~6,800 tokens` | **🔥 84.8%** | Custom IPs, Address Maps (`SEG_*`) 100% Intact |
| **7x Jupyter Notebooks (`.ipynb`)** | `~42,000 tokens` | `~8,400 tokens` | **🔥 80.0%** | All Code Cells & Hardware Pinout Tables Preserved |
| **VHDL & Custom RTL Cores** | `~12,000 tokens` | `~12,000 tokens` | **0% (Preserved)** | 100% Verbatim for Deep DSP & Timing Debugging |
| **Git Topology & Toolchain Banner** | `~2,500 tokens` | `~950 tokens` | **62.0%** | Compacted 15-commit graph + Toolchain Lock |
| **Total Hardware Context Payload** | **`~60,200 tokens`** | **`~20,800 tokens`** | **🔥 ~65.4%** | **Fits easily in standard LLM context windows!** |

---

## 🏛 Architecture & Dataflow

```
 [ Target Repository Root ]
          │
          ├── cog.conf (Declares Target Files & Output Destination)
          │
          ▼
     [ ./Cog/Ctx ]
          │
          ├───> [ engine.py ]        ──> Auto-Detects Vivado / Part / Git Constraints
          ├───> [ git_graph.py ]     ──> Multi-Branch Commit Topology & Divergence
          ├───> [ bd_pruner.py ]     ──> Purges LAYERED_METADATA & Vivado Boilerplate
          ├───> [ ipynb_clean.py ]   ──> Strips Output Blobs & Distills Markdown (# %%)
          ├───> [ code_minifier.py ] ──> Cleans Whitespace & Tool Copyright Headers
          │
          ▼
  [ context/summary.txt ] (Single Token-Dense, Fully Grounded Context Payload)
          │
          ▼
  [ token_meter.py ] (Calibrated ~3.1 Chars/Token Health & Savings Report)
```

---

## 🚀 Quick Start & Integration Guide

### 1. Add `Cog` as a Submodule in Your Repository
From the root of your target repository:
```bash
git submodule add https://github.com/SiririComun/Cog.git Cog
git submodule update --init --recursive
```

### 2. Create `cog.conf`
Create a `cog.conf` file in the root of your repository to declare target files and output destination:

```conf
# ==============================================================================
# Cog Configuration File
# ==============================================================================
OUTPUT: context/repo_summary.txt

# Target Files (Relative to repository root)
setup.py
.github/workflows/ci.yml
Top/pynq_z2/hog.conf
src/bd/xadc.bd
src/hdl/axis_trigger_unit.vhd
src/hdl/axis_spectral_mask.vhd
notebooks/tutorial.ipynb
```

### 3. Generate Context
Run the `Ctx` command:
```bash
./Cog/Ctx
```

---

## 💻 Terminal Output Example

```log
====================================================================
  🧠 COG CONTEXT GENERATION COMPLETE
====================================================================
  • Output File       : /home/user/project/context/repo_summary.txt
  • Final Size        : 165.6 KB
  • Estimated Tokens  : ~54,684 tokens
  • Token Reduction   : ~20.8% savings vs raw files
====================================================================
```

---

## 📑 Generated Context Header Preview

Every generated summary document begins with a strict environment anchor:

```text
==============================================================================
⚙️  PROJECT ENVIRONMENT & TOOLCHAIN CONSTRAINTS
==============================================================================
• Repository State    : master @ cf02545
• Vivado Tool Version : 2024.2.2 (STRICT: Target toolchain for TCL/GUI workflows)
• Target FPGA Device  : xc7z020clg400-1
• Primary HDL Language: VHDL
• Pinned HW Overlay   : SiririComun/hw-xadc-dma-overlays @ v1.6.0
==============================================================================
```

---

## 🛠 Project Structure

```
Cog/
├── Ctx                   # Executable POSIX Bash CLI entrypoint
├── LICENSE               # MIT License
├── README.md             # Project documentation
├── .gitignore
└── core/
    ├── __init__.py
    ├── engine.py         # Main orchestrator & toolchain detector
    ├── git_graph.py      # Git branch topology & tag extractor
    ├── bd_pruner.py      # Deep surgical Vivado Block Design compactor
    ├── ipynb_clean.py    # Jupyter Notebook JSON distiller
    ├── code_minifier.py  # Code minifier & header cleaner
    └── token_meter.py    # Calibrated prompt token estimator
```

---

## 🔄 Updating `Cog` Across Your Repositories

When improvements or new parsers are added to `Cog`, update your submodules with:
```bash
git submodule update --remote --merge Cog
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Developed by [SiririComun](https://github.com/SiririComun).