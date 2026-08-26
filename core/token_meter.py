class TokenMeter:
    """Estimates LLM prompt tokens (~4 characters/token heuristic) and prints health metrics."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        return len(text) // 4

    @classmethod
    def print_report(cls, original_size_bytes: int, final_text: str, output_path: str):
        final_size_bytes = len(final_text.encode("utf-8"))
        est_tokens = cls.estimate_tokens(final_text)
        
        reduction = 0.0
        if original_size_bytes > 0:
            reduction = max(0.0, (1.0 - (final_size_bytes / original_size_bytes)) * 100.0)

        print("\n" + "=" * 65)
        print("  🧠 COG CONTEXT GENERATION COMPLETE")
        print("=" * 65)
        print(f"  • Output File       : {output_path}")
        print(f"  • Final Size        : {final_size_bytes / 1024:.1f} KB")
        print(f"  • Estimated Tokens  : ~{est_tokens:,} tokens")
        if original_size_bytes > 0:
            print(f"  • Token Reduction   : ~{reduction:.1f}% savings vs raw files")
        print("=" * 65 + "\n")