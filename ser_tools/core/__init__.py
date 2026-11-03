"""Núcleo da s_SER_Tools: configurações, logging rico, utilitários e gerador de relatórios."""

from .config import SuiteConfig
from .logger import get_console, setup_logger
from .reporter import SecurityFinding, SecurityReport, SeverityLevel
from .utils import calculate_sha256, format_bytes, sanitize_target_name

__all__ = [
    "SuiteConfig",
    "get_console",
    "setup_logger",
    "SecurityFinding",
    "SecurityReport",
    "SeverityLevel",
    "calculate_sha256",
    "format_bytes",
    "sanitize_target_name",
]
