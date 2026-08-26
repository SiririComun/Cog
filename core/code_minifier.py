import re


class CodeMinifier:
    """Strips repeated license headers, trailing whitespace, and excess blank lines."""

    LICENSE_PATTERNS = [
        re.compile(r"--\s*Copyright\s+1986-20\d{2}\s+Xilinx,?\s+Inc\..*?(?=\n\s*\n|\Z)", re.DOTALL | re.IGNORECASE),
        re.compile(r"--\s*Tool Version: Vivado.*?(?=\n\s*\n|\Z)", re.DOTALL | re.IGNORECASE),
    ]

    @classmethod
    def minify(cls, text: str, ext: str) -> str:
        # 1. Strip Vivado auto-generated headers on VHDL files
        if ext in (".vhd", ".vhdl"):
            for pat in cls.LICENSE_PATTERNS:
                text = pat.sub("", text)

        # 2. Collapse 3+ consecutive blank lines to a single blank line
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        # 3. Strip trailing whitespace per line
        lines = [l.rstrip() for l in text.splitlines()]
        return "\n".join(lines).strip()