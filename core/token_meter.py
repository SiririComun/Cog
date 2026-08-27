#!/usr/bin/env python3
"""
Cog: Token Meter & Compaction Reporter (token_meter.py)
Estimates LLM prompt token consumption using syntax-calibrated heuristics (~3.1 chars/token)
and reports context health and reduction metrics.
"""

from typing import Optional


class TokenMeter:
    """
    Syntax-calibrated prompt token estimator and console reporter.
    Calibrated against modern BPE/SentencePiece tokenizers (Gemini / Claude / GPT).
    """

    # Calibrated character-to-token ratio for code, JSON, VHDL, and Markdown
    CHARS_PER_TOKEN = 3.1

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimates token count based on code/JSON character density."""
        if not text:
            return 0
        return int(round(len(text) / cls.CHARS_PER_TOKEN))

    @classmethod
    def print_report(
        cls,
        original_size_bytes: int,
        final_text: str,
        output_path: str,
    ):
        """Prints a clean summary of final payload size, estimated tokens, and savings."""
        final_size_bytes = len(final_text.encode("utf-8"))
        est_tokens = cls.estimate_tokens(final_text)

        # Estimate original tokens for accurate reduction calculation
        original_tokens = (
            int(round(original_size_bytes / cls.CHARS_PER_TOKEN))
            if original_size_bytes > 0
            else 0
        )

        reduction = 0.0
        if original_size_bytes > 0:
            reduction = max(
                0.0,
                (1.0 - (final_size_bytes / original_size_bytes)) * 100.0,
            )

        print("\n" + "=" * 68)
        print("  🧠 COG CONTEXT GENERATION COMPLETE")
        print("=" * 68)
        print(f"  • Output File       : {output_path}")
        print(f"  • Final Size        : {final_size_bytes / 1024:.1f} KB")
        print(f"  • Estimated Tokens  : ~{est_tokens:,} tokens")
        if original_size_bytes > 0:
            print(
                f"  • Token Reduction   : ~{reduction:.1f}% savings vs raw files"
            )
        print("=" * 68 + "\n")