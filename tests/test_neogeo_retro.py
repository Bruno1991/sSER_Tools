"""Testes unitários para o módulo de engenharia reversa de ROMs Neo Geo e extração de sprites."""

from pathlib import Path
import tempfile
import unittest
import numpy as np

from ser_tools.retro.neogeo_palette import NeoGeoPalette
from ser_tools.retro.neogeo_tile_decoder import NeoGeoTileDecoder
from ser_tools.retro.neogeo_rom import NeoGeoRomPackage
from ser_tools.retro.sprite_extractor import NeoGeoSpriteExtractor


class TestNeoGeoRetro(unittest.TestCase):
    def test_palette_color_word_decoding(self):
        # 0x0000 -> Preto puro
        black = NeoGeoPalette.decode_color_word(0x0000)
        self.assertEqual(black, (0, 0, 0, 255))

        # 0x7FFF -> Branco puro (todos os 15 bits ligados)
        white = NeoGeoPalette.decode_color_word(0x7FFF)
        self.assertEqual(white, (255, 255, 255, 255))

        # 0x0F00 -> Vermelho (R4-R1 = 15, R0 = 0 -> R = 30/31)
        red_word = (0xF << 8)
        red = NeoGeoPalette.decode_color_word(red_word)
        self.assertGreater(red[0], 240)
        self.assertEqual(red[1], 0)
        self.assertEqual(red[2], 0)

    def test_palette_presets(self):
        p1 = NeoGeoPalette.get_preset("arcade_p1")
        self.assertEqual(len(p1), 16)
        self.assertEqual(p1[0], (0, 0, 0, 0), "Cor 0 deve ser transparente")

        contrast = NeoGeoPalette.get_preset("contrast")
        self.assertEqual(len(contrast), 16)
        self.assertEqual(contrast[0], (0, 0, 0, 0))

    def test_decode_sprite_tile_synthetic(self):
        # Cria dados sintéticos para 64 bytes ímpares e 64 bytes pares
        odd = bytearray(64)
        even = bytearray(64)

        # No Bloco 0 (Top-Right: x=8..15, y=0..7), linha 0:
        # bp0 = 0xFF (bitplane 0 = 1 para todos os 8 pixels)
        # bp1 = 0x00
        # bp2 = 0xFF (bitplane 2 = 1 para todos os 8 pixels)
        # bp3 = 0x00
        # Cor resultante esperada = (0<<3) | (1<<2) | (0<<1) | 1 = 5
        odd[0] = 0xFF   # bp0
        odd[1] = 0x00   # bp1
        even[0] = 0xFF  # bp2
        even[1] = 0x00  # bp3

        matrix = NeoGeoTileDecoder.decode_sprite_tile(bytes(odd), bytes(even))
        self.assertEqual(matrix.shape, (16, 16))
        # Top-Right é x=8..15, y=0
        for px in range(8, 16):
            self.assertEqual(matrix[0, px], 5)
        # Outras posições devem ser 0
        self.assertEqual(matrix[0, 0], 0)
        self.assertEqual(matrix[8, 8], 0)

    def test_decode_fix_tile_synthetic(self):
        chunk = bytearray(32)
        # Bytes 16..23 são colunas 0 e 1.
        # Linha 0 (byte 16): valor 0x43 -> pixel esquerdo = 3, pixel direito = 4
        chunk[16] = 0x43

        matrix = NeoGeoTileDecoder.decode_fix_tile(bytes(chunk))
        self.assertEqual(matrix.shape, (8, 8))
        self.assertEqual(matrix[0, 0], 3)
        self.assertEqual(matrix[0, 1], 4)
        self.assertEqual(matrix[0, 2], 0)

    def test_kof98_rom_package_if_present(self):
        kof_zip = Path(r"C:\dev\s_SER_Tools\file\kof98.zip")
        if not kof_zip.is_file():
            self.skipTest("kof98.zip não encontrado em file/")

        pkg = NeoGeoRomPackage(kof_zip)
        self.assertEqual(len(pkg.c_pairs), 4, "KOF98 deve conter 4 pares de C-ROMs")
        self.assertEqual(pkg.total_sprite_tiles, 524288, "KOF98 deve ter 524.288 tiles")
        self.assertIsNotNone(pkg.s_rom, "Fix ROM (S1) deve estar presente")
        self.assertEqual(len(pkg.p_roms), 2, "KOF98 deve ter 2 P-ROMs")

        # Teste de extração de sheet
        extractor = NeoGeoSpriteExtractor(pkg)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            sheet = extractor.extract_sheet(
                pair_index=1,
                start_tile=1,
                count=16,
                cols=4,
                output_path=tmp_path,
            )
            self.assertEqual(sheet.size, (4 * 16, 4 * 16))
            self.assertTrue(tmp_path.is_file())
            self.assertGreater(tmp_path.stat().st_size, 100)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
