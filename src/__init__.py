"""Análise do grafo email-EuAll (SNAP)."""

import sys

# No Windows, quando a saída é redirecionada (arquivo/pipe), o Python usa a
# codificação ANSI (cp1252), que não tem símbolos como ∞, σ, γ e →. Forçamos
# UTF-8 nesses casos para que `python -m src.<modulo> > saida.txt` funcione.
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure") \
            and (_stream.encoding or "").lower().replace("-", "") != "utf8":
        _stream.reconfigure(encoding="utf-8")
