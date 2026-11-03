#!/usr/bin/env python3
"""Diagnóstico de ambiente e ferramentas para s_SER_Tools."""

import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path se executado a partir de scripts/
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from ser_tools.cli.main_cli import main

if __name__ == "__main__":
    sys.exit(main(["doctor"]))

