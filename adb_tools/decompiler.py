"""Fachada de compatibilidade retroativa para adb_tools.decompiler."""

from ser_tools.android.decompiler import (
    ApkDecompiler,
    DecompileResult,
    JadxManager,
    JavaEnvironment,
)

__all__ = [
    "ApkDecompiler",
    "DecompileResult",
    "JadxManager",
    "JavaEnvironment",
]
