"""Utilitários transversais para a suíte s_SER_Tools.

Fornece funções auxiliares de formatação de grandezas, cálculo de hashes criptográficos
e sanitização de caminhos e nomes de recursos.
"""

import hashlib
from pathlib import Path
import re
from typing import Union


def format_bytes(size: Union[int, float]) -> str:
    """Formata bytes em B, KB, MB, GB ou TB de forma legível e precisa."""
    size_float = float(size)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024.0:
            return f"{size_float:.2f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.2f} TB"


def calculate_sha256(file_path: Union[str, Path], chunk_size: int = 65536) -> str:
    """Calcula o hash SHA-256 de um arquivo de forma eficiente via streaming."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def sanitize_target_name(name: str) -> str:
    """Sanitiza strings de identificadores de pacotes ou arquivos para nomes seguros em disco."""
    clean = re.sub(r'[^\w\.-]', '_', name.strip())
    return clean or "unnamed_target"
