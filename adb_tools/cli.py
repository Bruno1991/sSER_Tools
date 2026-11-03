"""Fachada de compatibilidade retroativa para adb_tools.cli.

Permite que scripts legados e testes acessem format_bytes e invoquem a CLI unificada.
"""

import sys
from typing import List, Optional

from ser_tools.cli.main_cli import main
from ser_tools.core.utils import format_bytes

__all__ = ["format_bytes", "main"]


if __name__ == "__main__":
    sys.exit(main())
