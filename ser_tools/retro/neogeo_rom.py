"""Analisador e gerenciador de pacotes de ROM Arcade Neo Geo (MVS / AES).

Classifica automaticamente os arquivos internos de um pacote ZIP de acordo com a arquitetura SNK:
- P-ROMs: Código do processador Motorola 68000
- C-ROMs: Sprites e gráficos LSPC (pares ímpar/par)
- S-ROM: Camada fixa de texto e HUD (8x8)
- M-ROM: Código do coprocessador de áudio Zilog Z80
- V-ROMs: Amostras PCM/ADPCM do sintetizador Yamaha YM2610
"""

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import zipfile


@dataclass
class RomFileInfo:
    name: str
    size_bytes: int
    category: str
    crc32: Optional[str] = None


@dataclass
class CPairInfo:
    pair_index: int
    odd_rom: str
    even_rom: str
    pair_tiles: int


class NeoGeoRomPackage:
    """Carrega e inspeciona um pacote ZIP de ROM Neo Geo."""

    def __init__(self, zip_path: Path | str):
        self.zip_path = Path(zip_path).resolve()
        if not self.zip_path.is_file():
            raise FileNotFoundError(f"Arquivo de ROM não encontrado: {self.zip_path}")

        self.rom_files: Dict[str, RomFileInfo] = {}
        self.p_roms: List[str] = []
        self.c_pairs: List[CPairInfo] = []
        self.s_rom: Optional[str] = None
        self.m_rom: Optional[str] = None
        self.v_roms: List[str] = []
        self.total_sprite_tiles = 0

        self._scan_archive()

    def _scan_archive(self) -> None:
        """Examina o índice ZIP e classifica as ROMs por categoria de barramento."""
        with zipfile.ZipFile(self.zip_path, "r") as z:
            # Dicionário temporário de arquivos C
            c_roms_dict: Dict[int, str] = {}

            for info in z.infolist():
                fname = info.filename
                fsize = info.file_size
                crc_str = f"{info.CRC:08X}" if info.CRC else None

                # Ignora diretórios e metadados
                if fname.endswith("/") or fname.lower().endswith(".html") or fname.lower().endswith(".txt"):
                    continue

                category = "UNKNOWN"
                lower = fname.lower()

                # P-ROM (Motorola 68000)
                if re.search(r"[-_.]p[0-9]+", lower) or "prom" in lower:
                    category = "P_ROM"
                    self.p_roms.append(fname)
                # S-ROM (Fix layer)
                elif re.search(r"[-_.]s[0-9]+", lower) or "srom" in lower or "sfix" in lower:
                    category = "S_ROM"
                    self.s_rom = fname
                # M-ROM (Z80 Sound)
                elif re.search(r"[-_.]m[0-9]+", lower) or "mrom" in lower:
                    category = "M_ROM"
                    self.m_rom = fname
                # V-ROM (ADPCM Audio)
                elif re.search(r"[-_.]v[0-9]+", lower) or "vrom" in lower:
                    category = "V_ROM"
                    self.v_roms.append(fname)
                # C-ROM (Sprites)
                elif re.search(r"[-_.]c([0-9]+)", lower):
                    category = "C_ROM"
                    m = re.search(r"[-_.]c([0-9]+)", lower)
                    if m:
                        c_num = int(m.group(1))
                        c_roms_dict[c_num] = fname

                self.rom_files[fname] = RomFileInfo(
                    name=fname,
                    size_bytes=fsize,
                    category=category,
                    crc32=crc_str,
                )

            # Agrupa os pares de C-ROMs (1 com 2, 3 com 4, 5 com 6, 7 com 8...)
            c_numbers = sorted(c_roms_dict.keys())
            pair_idx = 1
            for i in range(0, len(c_numbers) - 1, 2):
                odd_num = c_numbers[i]
                even_num = c_numbers[i + 1]
                odd_name = c_roms_dict[odd_num]
                even_name = c_roms_dict[even_num]

                odd_size = self.rom_files[odd_name].size_bytes
                even_size = self.rom_files[even_name].size_bytes
                # Cada tile usa 64 bytes em cada ROM
                tiles = min(odd_size, even_size) // 64
                self.total_sprite_tiles += tiles

                self.c_pairs.append(
                    CPairInfo(
                        pair_index=pair_idx,
                        odd_rom=odd_name,
                        even_rom=even_name,
                        pair_tiles=tiles,
                    )
                )
                pair_idx += 1

            self.p_roms.sort()
            self.v_roms.sort()

    def get_c_pair_data(self, pair_index: int = 1) -> Tuple[bytes, bytes]:
        """Carrega em memória os bytes brutos de um par de C-ROMs (ímpar e par)."""
        if pair_index < 1 or pair_index > len(self.c_pairs):
            raise IndexError(f"Índice de par inválido: {pair_index}. Disponíveis: 1 a {len(self.c_pairs)}")

        target_pair = self.c_pairs[pair_index - 1]
        with zipfile.ZipFile(self.zip_path, "r") as z:
            odd_data = z.read(target_pair.odd_rom)
            even_data = z.read(target_pair.even_rom)
        return odd_data, even_data

    def get_s_rom_data(self) -> Optional[bytes]:
        """Carrega os dados da ROM de camada fixa (Fix layer), se presente."""
        if not self.s_rom:
            return None
        with zipfile.ZipFile(self.zip_path, "r") as z:
            return z.read(self.s_rom)

    def get_p_rom_data(self) -> Optional[bytes]:
        """Carrega o código do programa da primeira P-ROM."""
        if not self.p_roms:
            return None
        with zipfile.ZipFile(self.zip_path, "r") as z:
            return z.read(self.p_roms[0])

    def inspect(self) -> Dict[str, Any]:
        """Retorna metadados estruturados do pacote de ROM."""
        return {
            "archive_name": self.zip_path.name,
            "archive_size_bytes": self.zip_path.stat().st_size,
            "total_c_pairs": len(self.c_pairs),
            "total_sprite_tiles": self.total_sprite_tiles,
            "total_sprite_bytes": self.total_sprite_tiles * 128,
            "c_pairs": [
                {
                    "pair": p.pair_index,
                    "odd_rom": p.odd_rom,
                    "even_rom": p.even_rom,
                    "tiles": p.pair_tiles,
                }
                for p in self.c_pairs
            ],
            "fix_rom": self.s_rom,
            "fix_tiles": (self.rom_files[self.s_rom].size_bytes // 32) if self.s_rom else 0,
            "program_roms": self.p_roms,
            "sound_roms": {"m_rom": self.m_rom, "v_roms": self.v_roms},
        }

