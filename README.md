# 🧠 Cog — Context on Git

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Standard%20Library)-brightgreen.svg)]()
[![Git Submodule Pattern](https://img.shields.io/badge/Pattern-Git%20Submodule-blueviolet.svg)]()
[![Release](https://img.shields.io/badge/Release-v0.1.0-orange.svg)](https://github.com/SiririComun/Cog/releases)

> **High-density, token-optimized codebase context distillation for LLMs and AI-assisted engineering.**

Inspired by [CERN's Hog (HDL on Git)](https://cern.ch/hog), **Cog** is a lightweight, zero-dependency Git submodule utility designed to extract, prune, and format complex multi-branch hardware (FPGA/ASIC), software (Python/C++), and Jupyter Notebook repositories into a single compact context document optimized for Large Language Models (GPT, Claude, Gemini).

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
* 📉 **Aggressive Token Optimization (60%–80% Savings):**
  * **Vivado Block Design Pruning (`.bd`):** Strips thousands of lines of default Zynq/MicroBlaze MIO & DDR boilerplate while preserving 100% of custom IP instances, parameter overrides, AXI interconnects, and memory maps.
  * **Jupyter Notebook Stripper (`.ipynb`):** Strips execution counters, cell IDs, output blobs, and base64 images, extracting clean Python code blocks and markdown commentary in `# %%` script format.
  * **Source Code Minification:** Strips auto-generated tool copyright headers and collapses redundant whitespace.
* 🌳 **Multi-Branch Git Topology & Status:** Captures full ASCII commit graphs across all local/remote branches, active tags, tracking divergence, and working-tree dirty status.
* 📦 **Git Submodule Workflow:** Drop `Cog` into any repository in 2 commands and update it across projects with `git submodule update --remote`.
* 📊 **Built-in Token Meter:** Estimates prompt token consumption and displays compression ratio reports in the terminal.

---

## 📊 Token Compression Benchmarks

Real-world token benchmark measured on the [PYNQ Oscilloscope & Spectrum Analyzer](https://github.com/SiririComun/sw-pynq-oscilloscope) project:

| Artifact / File Type | Raw Ingestion Size | Cog Compacted Size | Token Savings | Semantic Integrity |
| :--- | :---: | :---: | :---: | :---: |
| **Vivado Block Design (`xadc.bd`)** | `~18,500 tokens` | `~3,200 tokens` | **82.7%** | Custom IPs, Nets & Address Map 100% Intact |
| **7x Jupyter Notebooks (`.ipynb`)** | `~42,000 tokens` | `~8,400 tokens` | **80.0%** | Full Tutorial Descriptions & Code Preserved |
| **VHDL & Custom RTL Cores** | `~14,200 tokens` | `~11,100 tokens` | **21.8%** | Logic, Generics & Processes Preserved |
| **Total Context Footprint** | **`~74,700 tokens`** | **`~22,700 tokens`** | **🔥 69.6%** | **Fits easily in standard LLM context windows!** |

---

## 🏛 Architecture & Dataflow

```
 [ Target Repository Root ]
          │
          ├── cog.conf (Specifies Target Files & Output Destination)
          │
          ▼
     [ ./Cog/Ctx ]
          │
          ├───> [ git_graph.py ]     ──> Multi-Branch Commit Topology & Tags
          ├───> [ bd_pruner.py ]     ──> Strips Vivado Default Zynq Boilerplate
          ├───> [ ipynb_clean.py ]   ──> Strips Notebook Blobs -> Clean Python (# %%)
          ├───> [ code_minifier.py ] ──> Minifies RTL / Source Code
          │
          ▼
  [ context/summary.txt ] (Single Token-Dense Context Payload)
          │
          ▼
  [ token_meter.py ] (Console Health & Token Reduction Report)
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
src/bd/system.bd
src/hdl/top.vhd
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
=================================================================
  🧠 COG CONTEXT GENERATION COMPLETE
=================================================================
  • Output File       : /home/user/project/context/repo_summary.txt
  • Final Size        : 142.4 KB
  • Estimated Tokens  : ~36,450 tokens
  • Token Reduction   : ~71.2% savings vs raw files
=================================================================
```

---

## 🛠 Project Structure

```
Cog/
├── Ctx                   # Executable CLI entrypoint
├── LICENSE               # MIT License
├── README.md             # Project documentation
├── .gitignore
└── core/
    ├── __init__.py
    ├── engine.py         # Main orchestrator & command dispatcher
    ├── git_graph.py      # Git branch topology & tag extractor
    ├── bd_pruner.py      # Vivado Block Design JSON compactor
    ├── ipynb_clean.py    # Jupyter Notebook JSON stripper
    ├── code_minifier.py  # Code minifier & header cleaner
    └── token_meter.py    # Token estimator & reporting engine
```

---

## 🔄 Updating `Cog` Across Your Repositories

When improvements or new parsers are added to `Cog`, update your submodules with:
```bash
git submodule update --remote Cog
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Developed with ❤️ by [Juan Pablo Sánchez (SiririComun)](https://github.com/SiririComun).