#!/usr/bin/env python3
"""
Cog: Token Meter & Compaction Reporter (token_meter.py)
Estimates LLM prompt token consumption using calibrated heuristics (~3.62 chars/token),
evaluates model context window tiers, and reports context health and reduction metrics.
"""

from typing import Optional, Tuple


class TokenMeter:
    """
    Syntax-calibrated prompt token estimator and console reporter.
    Calibrated against modern BPE/SentencePiece tokenizers (Claude / GPT-4 / Gemini).
    """

    # Calibrated character-to-token ratio for code, Python, JSON, and Markdown
    CHARS_PER_TOKEN = 3.62

    # Context window threshold tiers
    TIER_COMPACT = 32768      # 32k: Universal local & cloud models
    TIER_STANDARD = 131072    # 128k: GPT-4o / standard frontier window
    TIER_EXTENDED = 200000    # 200k: Claude 3.5 / Gemini extended window

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimates token count based on modern LLM subword tokenizer density."""
        if not text:
            return 0
        return int(round(len(text) / cls.CHARS_PER_TOKEN))

    @classmethod
    def get_model_compatibility(cls, est_tokens: int) -> Tuple[str, str]:
        """Returns compatibility badge and recommendation based on token footprint."""
        if est_tokens < cls.TIER_COMPACT:
            return "🟢 Universal", "Fits all models (GPT-4o, Claude 3.5, Gemini, Llama 3, Local 32k)"
        elif est_tokens < cls.TIER_STANDARD:
            return "🟡 Standard", "Fits standard flagship models (GPT-4o, Claude 3.5, Gemini 1.5)"
        elif est_tokens < cls.TIER_EXTENDED:
            return "🟠 Extended", "Fits extended-window models (Claude 3.5 200k, Gemini 1.5 Pro)"
        else:
            return "🔴 Ultra-Large", "Exceeds 200k tokens; recommend domain slicing (./Cog/Ctx sw / rtl / bd)"

    @classmethod
    def print_report(
        cls,
        original_size_bytes: int,
        final_text: str,
        output_path: str,
    ):
        """Prints a clean summary of final payload size, estimated tokens, compatibility, and savings."""
        final_size_bytes = len(final_text.encode("utf-8"))
        est_tokens = cls.estimate_tokens(final_text)
        tier_badge, tier_desc = cls.get_model_compatibility(est_tokens)

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
        print(f"  • Estimated Tokens  : ~{est_tokens:,} tokens ({tier_badge})")
        print(f"  • Model Target      : {tier_desc}")
        if original_size_bytes > 0 and reduction > 0.1:
            print(f"  • Token Reduction   : ~{reduction:.1f}% savings vs raw files")
        print("=" * 68 + "\n")