#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

# Ensure core directory is accessible
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from tex_clean import TexCleaner


class TestTexCleaner(unittest.TestCase):
    def test_clean_tex_comments_and_escapes(self):
        raw_tex = r"""
% !TeX root = main.tex
% Borrador antiguo que debe ser eliminado
\section{Resultados y Discusion}
El margen de error obtenido fue del 4.5\% en las mediciones. % Comentario inline a eliminar

% Otro parrafo comentado completo
\begin{equation}
    y[n] = x[n] * h[n] % Convolucion discreta
\end{equation}
"""
        cleaned = TexCleaner.clean_tex(raw_tex)

        self.assertIn(r"% !TeX root = main.tex", cleaned)
        self.assertIn(r"\section{Resultados y Discusion}", cleaned)
        self.assertIn(r"4.5\% en las mediciones.", cleaned)
        self.assertNotIn("Comentario inline a eliminar", cleaned)
        self.assertNotIn("Borrador antiguo que debe ser eliminado", cleaned)
        self.assertNotIn("Otro parrafo comentado completo", cleaned)
        self.assertNotIn("Convolucion discreta", cleaned)

    def test_clean_tex_preserves_verbatim(self):
        raw_tex = r"""
\begin{verbatim}
# Codigo Python literal
error = count % 2 # No debe borrarse este comentario
\end{verbatim}
"""
        cleaned = TexCleaner.clean_tex(raw_tex)

        self.assertIn(r"# Codigo Python literal", cleaned)
        self.assertIn(r"error = count % 2 # No debe borrarse este comentario", cleaned)

    def test_clean_bib_purges_abstract_and_file(self):
        raw_bib = r"""
@article{sanchez2026walo,
  author    = {Sanchez, Juan Pablo and Comun, Siriri},
  title     = {FPGA-Accelerated Acoustic Localization},
  journal   = {IEEE Transactions on Instrumentation},
  year      = {2026},
  volume    = {42},
  pages     = {100--115},
  doi       = {10.1109/TIM.2026.001},
  abstract  = {In this paper, we present a novel hardware architecture
               for real-time sound localization using PYNQ-Z2 boards.
               Extensive benchmarks show a 10x acceleration.},
  file      = {:path/to/local/pdf/sanchez2026.pdf:PDF}
}
"""
        cleaned = TexCleaner.clean_bib(raw_bib)

        self.assertIn("author    = {Sanchez, Juan Pablo and Comun, Siriri}", cleaned)
        self.assertIn("title     = {FPGA-Accelerated Acoustic Localization}", cleaned)
        self.assertIn("year      = {2026}", cleaned)
        self.assertIn("doi       = {10.1109/TIM.2026.001}", cleaned)
        self.assertNotIn("In this paper, we present a novel hardware architecture", cleaned)
        self.assertNotIn("sanchez2026.pdf", cleaned)


if __name__ == "__main__":
    unittest.main()