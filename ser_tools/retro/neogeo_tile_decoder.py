"""Decodificador de alta performance para os formatos de tiles do SNK Neo Geo.

Suporta:
1. Sprite Tiles (16x16 pixels, 4BPP planar, 128 bytes distribuídos entre pares C-ROMs).
   - Organizados em 4 blocos de 8x8 na ordem de quadrantes: Top-Right, Bottom-Right, Top-Left, Bottom-Left.
   - Bitplanes 0 e 1 no C-ROM ímpar (C1, C3, C5, C7).
   - Bitplanes 2 e 3 no C-ROM par (C2, C4, C6, C8).
2. Fix Layer Tiles (8x8 pixels, 4BPP, 32 bytes no S-ROM).
   - Organizados em colunas verticais com pares de pixels invertidos nos nibbles.
"""

from typing import List, Optional
import numpy as np


class NeoGeoTileDecoder:
    """Decodificador vetorizado de tiles do subsistema gráfico LSPC do Neo Geo."""

    # Tabela de expansão rápida de bits: para cada byte (0..255), gera os 8 bits [MSB..LSB]
    _BIT_TABLE = np.array(
        [[(b >> (7 - i)) & 1 for i in range(8)] for b in range(256)],
        dtype=np.uint8,
    )

    # Offsets de coordenadas (x_offset, y_offset) para os quatro blocos de 8x8 de um tile 16x16
    _BLOCK_OFFSETS = [
        (8, 0),  # Bloco 0: Top-Right
        (8, 8),  # Bloco 1: Bottom-Right
        (0, 0),  # Bloco 2: Top-Left
        (0, 8),  # Bloco 3: Bottom-Left
    ]

    @classmethod
    def decode_sprite_tile(cls, c_odd_chunk: bytes, c_even_chunk: bytes) -> np.ndarray:
        """Decodifica um tile de sprite de 16x16 (64 bytes do C-ROM ímpar + 64 bytes do C-ROM par).

        Retorna:
            np.ndarray de forma (16, 16) com índices de paleta de 0 a 15 (uint8).
        """
        tile_matrix = np.zeros((16, 16), dtype=np.uint8)

        for block_idx, (x_ofs, y_ofs) in enumerate(cls._BLOCK_OFFSETS):
            base_offset = block_idx * 16
            for row in range(8):
                idx = base_offset + row * 2
                bp0 = c_odd_chunk[idx]
                bp1 = c_odd_chunk[idx + 1]
                bp2 = c_even_chunk[idx]
                bp3 = c_even_chunk[idx + 1]

                # Combina os 4 bitplanes em um array de 8 pixels
                # pixel[p] = (bp3[p] << 3) | (bp2[p] << 2) | (bp1[p] << 1) | bp0[p]
                pixels_8 = (
                    (cls._BIT_TABLE[bp3] << 3)
                    | (cls._BIT_TABLE[bp2] << 2)
                    | (cls._BIT_TABLE[bp1] << 1)
                    | cls._BIT_TABLE[bp0]
                )
                tile_matrix[y_ofs + row, x_ofs : x_ofs + 8] = pixels_8

        return tile_matrix

    @classmethod
    def decode_fix_tile(cls, s_chunk: bytes) -> np.ndarray:
        """Decodifica um tile de camada fixa (Fix layer / HUD) de 8x8 (32 bytes do S-ROM).

        Ordem de armazenamento em colunas:
            Bytes 16..23: Colunas 0 e 1 (linhas 0..7)
            Bytes 24..31: Colunas 2 e 3 (linhas 0..7)
            Bytes 0..7:   Colunas 4 e 5 (linhas 0..7)
            Bytes 8..15:  Colunas 6 e 7 (linhas 0..7)

        Em cada byte:
            Pixel esquerdo (coluna par): bits 0..3
            Pixel direito (coluna ímpar): bits 4..7

        Retorna:
            np.ndarray de forma (8, 8) com índices de paleta de 0 a 15 (uint8).
        """
        fix_matrix = np.zeros((8, 8), dtype=np.uint8)

        for line in range(8):
            # Colunas 0 e 1
            b_c01 = s_chunk[16 + line]
            fix_matrix[line, 0] = b_c01 & 0x0F
            fix_matrix[line, 1] = (b_c01 >> 4) & 0x0F

            # Colunas 2 e 3
            b_c23 = s_chunk[24 + line]
            fix_matrix[line, 2] = b_c23 & 0x0F
            fix_matrix[line, 3] = (b_c23 >> 4) & 0x0F

            # Colunas 4 e 5
            b_c45 = s_chunk[0 + line]
            fix_matrix[line, 4] = b_c45 & 0x0F
            fix_matrix[line, 5] = (b_c45 >> 4) & 0x0F

            # Colunas 6 e 7
            b_c67 = s_chunk[8 + line]
            fix_matrix[line, 6] = b_c67 & 0x0F
            fix_matrix[line, 7] = (b_c67 >> 4) & 0x0F

        return fix_matrix

