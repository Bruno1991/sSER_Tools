"""Gerenciador e decodificador de paletas de cor para o hardware SNK Neo Geo (MVS / AES).

O hardware Neo Geo utiliza palavras de 16 bits (RGB555 + Dark bit):
  Bit 15: Dark bit (modificador global de brilho)
  Bit 14: R0 (bit menos significativo do Vermelho)
  Bit 13: G0 (bit menos significativo do Verde)
  Bit 12: B0 (bit menos significativo do Azul)
  Bits 11-8: R4-R1 (bits mais significativos do Vermelho)
  Bits 7-4:  G4-G1 (bits mais significativos do Verde)
  Bits 3-0:  B4-B1 (bits mais significativos do Azul)
"""

from typing import Dict, List, Tuple

RGBA = Tuple[int, int, int, int]


class NeoGeoPalette:
    """Decodificador de cores e colecionador de paletas Neo Geo."""

    @staticmethod
    def decode_color_word(word: int) -> RGBA:
        """Converte uma palavra de 16 bits do formato Neo Geo para (R, G, B, A)."""
        # Extrai componentes de 5 bits (0..31)
        r5 = (((word >> 8) & 0x0F) << 1) | ((word >> 14) & 1)
        g5 = (((word >> 4) & 0x0F) << 1) | ((word >> 13) & 1)
        b5 = (((word >> 0) & 0x0F) << 1) | ((word >> 12) & 1)

        # Converte de 5 bits (0..31) para 8 bits (0..255)
        r8 = (r5 * 255) // 31
        g8 = (g5 * 255) // 31
        b8 = (b5 * 255) // 31

        # Aplica o dark bit se estiver ativo (atenuação sutil para tons escuros)
        if word & 0x8000:
            r8 = max(0, r8 - 14)
            g8 = max(0, g8 - 14)
            b8 = max(0, b8 - 14)

        return (r8, g8, b8, 255)

    @classmethod
    def decode_palette_16(cls, data: bytes, offset: int = 0, transparent_zero: bool = True) -> List[RGBA]:
        """Decodifica uma tabela de 16 cores (32 bytes) no formato big-endian do 68000."""
        palette: List[RGBA] = []
        for i in range(16):
            pos = offset + i * 2
            if pos + 2 <= len(data):
                word = (data[pos] << 8) | data[pos + 1]
                rgba = cls.decode_color_word(word)
                if i == 0 and transparent_zero:
                    palette.append((0, 0, 0, 0))  # Cor 0 é transparente no raster Neo Geo
                else:
                    palette.append(rgba)
            else:
                palette.append((0, 0, 0, 0) if i == 0 else (255, 255, 255, 255))
        return palette

    @staticmethod
    def get_preset(name: str = "arcade_p1") -> List[RGBA]:
        """Retorna perfis de paletas predefinidas para visualização de sprites e triagem forense."""
        presets: Dict[str, List[RGBA]] = {
            # Paleta autêntica de combate KOF: tons de pele, destaques quentes, uniformes e traços
            "arcade_p1": [
                (0, 0, 0, 0),         # 0: Transparente
                (248, 248, 248, 255), # 1: Branco / Highlight
                (240, 208, 176, 255), # 2: Pele Clara
                (224, 168, 128, 255), # 3: Pele Médio
                (184, 120, 80, 255),  # 4: Pele Sombra
                (128, 72, 48, 255),   # 5: Pele Sombra Profunda
                (248, 56, 0, 255),    # 6: Vermelho KOF
                (184, 32, 0, 255),    # 7: Vermelho Escuro
                (104, 16, 0, 255),    # 8: Carmim Profundo
                (0, 120, 248, 255),   # 9: Azul Real
                (0, 64, 184, 255),    # 10: Azul Médio
                (0, 24, 104, 255),    # 11: Azul Marinho
                (248, 216, 0, 255),   # 12: Dourado / Cabelo Loiro
                (168, 136, 0, 255),   # 13: Ouro Envelhecido
                (80, 80, 80, 255),    # 14: Cinza Neutro
                (16, 16, 16, 255),    # 15: Preto / Contorno
            ],
            # Paleta de Alto Contraste (análise forense de planos de bits e camadas)
            "contrast": [
                (0, 0, 0, 0),         # 0: Transparente
                (255, 255, 255, 255), # 1: Branco
                (255, 0, 0, 255),     # 2: Vermelho Vivo
                (255, 128, 0, 255),   # 3: Laranja
                (255, 255, 0, 255),   # 4: Amarelo
                (128, 255, 0, 255),   # 5: Chartreuse
                (0, 255, 0, 255),     # 6: Verde Lima
                (0, 255, 128, 255),   # 7: Verde Água
                (0, 255, 255, 255),   # 8: Ciano
                (0, 128, 255, 255),   # 9: Azul Claro
                (0, 0, 255, 255),     # 10: Azul Puro
                (128, 0, 255, 255),   # 11: Roxo
                (255, 0, 255, 255),   # 12: Magenta
                (255, 0, 128, 255),   # 13: Rosa Choque
                (160, 160, 160, 255), # 14: Prata
                (20, 20, 20, 255),    # 15: Quase Preto
            ],
            # Rampa monocromática de luminância linear (0..15)
            "grayscale": [
                (0, 0, 0, 0) if i == 0 else (i * 17, i * 17, i * 17, 255)
                for i in range(16)
            ],
            # Retro Neon CRT Arcade
            "neon_crt": [
                (0, 0, 0, 0),         # 0: Transparente
                (0, 255, 200, 255),   # 1: Ciano Fosforescente
                (0, 210, 170, 255),
                (0, 170, 140, 255),
                (0, 130, 110, 255),
                (0, 90, 80, 255),
                (255, 0, 128, 255),   # 6: Magenta Neon
                (200, 0, 100, 255),
                (150, 0, 75, 255),
                (100, 0, 50, 255),
                (255, 230, 0, 255),   # 10: Amarelo CRT
                (200, 180, 0, 255),
                (150, 130, 0, 255),
                (90, 90, 110, 255),
                (50, 50, 70, 255),
                (10, 10, 20, 255),    # 15: Fundo Escuro
            ],
        }
        return presets.get(name.lower(), presets["arcade_p1"])
