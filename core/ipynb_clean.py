import json


class NotebookCleaner:
    """Converts .ipynb JSON into a high-density, clean Python/Markdown format (saving ~75% tokens)."""

    @classmethod
    def clean_notebook(cls, raw_content: str) -> str:
        try:
            data = json.loads(raw_content)
        except Exception:
            return raw_content

        cells = data.get("cells", [])
        output_lines = []

        for idx, cell in enumerate(cells):
            cell_type = cell.get("cell_type", "")
            source = "".join(cell.get("source", [])).strip()

            if not source:
                continue

            if cell_type == "markdown":
                output_lines.append(f"# %% [markdown] Cell {idx + 1}")
                for line in source.splitlines():
                    output_lines.append(f"# {line}" if not line.startswith("#") else line)
                output_lines.append("")
            elif cell_type == "code":
                output_lines.append(f"# %% [code] Cell {idx + 1}")
                output_lines.append(source)
                output_lines.append("")

        return "\n".join(output_lines)