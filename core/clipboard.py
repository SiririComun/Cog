#!/usr/bin/env python3
"""
Cog: Cross-Platform Clipboard Manager (clipboard.py)
Copies context payloads directly to the system clipboard using native CLI utilities
(wl-copy, xclip, xsel, pbcopy, clip.exe, PowerShell Set-Clipboard).
"""

import shutil
import subprocess
import sys


class ClipboardManager:
    """
    Handles zero-dependency cross-platform clipboard copy operations.
    """

    @classmethod
    def copy(cls, text: str) -> bool:
        """Attempts to copy text to system clipboard. Returns True on success."""
        encoded_data = text.encode("utf-8")

        # 1. macOS (pbcopy)
        if sys.platform == "darwin" and shutil.which("pbcopy"):
            return cls._run_pipe(["pbcopy"], encoded_data)

        # 2. Windows (clip.exe or PowerShell)
        if sys.platform.startswith("win") or sys.platform == "cygwin":
            if shutil.which("clip.exe") or shutil.which("clip"):
                clip_bin = shutil.which("clip.exe") or "clip"
                return cls._run_pipe([clip_bin], encoded_data)
            if shutil.which("powershell"):
                return cls._run_pipe(["powershell", "-command", "Set-Clipboard"], encoded_data)

        # 3. Linux / BSD (Wayland: wl-copy, X11: xclip, xsel)
        if shutil.which("wl-copy"):
            return cls._run_pipe(["wl-copy"], encoded_data)

        if shutil.which("xclip"):
            return cls._run_pipe(["xclip", "-selection", "clipboard"], encoded_data)

        if shutil.which("xsel"):
            return cls._run_pipe(["xsel", "--clipboard", "--input"], encoded_data)

        return False

    @staticmethod
    def _run_pipe(cmd: list, data: bytes) -> bool:
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.communicate(input=data)
            return proc.returncode == 0
        except Exception:
            return False