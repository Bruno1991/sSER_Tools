"""Extrator e gerador de Sprite Sheets para ROMs Arcade Neo Geo.

Converte dados decodificados dos barramentos C-ROM e S-ROM em imagens PNG
com transparência alfa, folhas de contato (sprite sheets) e atlas de fontes.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union
import numpy as np
from PIL import Image

from .neogeo_palette import NeoGeoPalette, RGBA
from .neogeo_rom import NeoGeoRomPackage
from .neogeo_tile_decoder import NeoGeoTileDecoder


class NeoGeoSpriteExtractor:
    """Orquestrador de extração de gráficos e atlas de sprites Neo Geo."""

    def __init__(self, rom_package: NeoGeoRomPackage):
        self.rom = rom_package
        self.palette = NeoGeoPalette.get_preset("arcade_p1")

    def set_palette(self, palette_or_name: Union[str, List[RGBA]]) -> None:
        """Define a paleta ativa para renderização."""
        if isinstance(palette_or_name, str):
            self.palette = NeoGeoPalette.get_preset(palette_or_name)
        else:
            self.palette = palette_or_name

    def render_tile_image(self, tile_matrix: np.ndarray, scale: int = 1) -> Image.Image:
        """Converte uma matriz (H, W) de índices em uma imagem PIL RGBA."""
        h, w = tile_matrix.shape
        img = Image.new("RGBA", (w, h))
        palette_len = len(self.palette)

        # Mapeia cores
        for y in range(h):
            for x in range(w):
                idx = int(tile_matrix[y, x]) % palette_len
                img.putpixel((x, y), self.palette[idx])

        if scale > 1:
            img = img.resize((w * scale, h * scale), resample=Image.Resampling.NEAREST)
        return img

    def extract_sheet(
        self,
        pair_index: int,
        start_tile: int,
        count: int,
        cols: int = 16,
        output_path: Optional[Path] = None,
        scale: int = 1,
    ) -> Image.Image:
        """Gera uma folha de sprites (sprite sheet) a partir de um par de C-ROMs."""
        odd_data, even_data = self.rom.get_c_pair_data(pair_index)
        max_tiles = len(odd_data) // 64

        actual_count = min(count, max_tiles - start_tile)
        if actual_count <= 0:
            raise ValueError(f"Intervalo de tiles inválido: início {start_tile}, total disponível {max_tiles}")

        rows = (actual_count + cols - 1) // cols
        sheet_w = cols * 16
        sheet_h = rows * 16

        sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

        for i in range(actual_count):
            tile_idx = start_tile + i
            chunk_odd = odd_data[tile_idx * 64 : (tile_idx + 1) * 64]
            chunk_even = even_data[tile_idx * 64 : (tile_idx + 1) * 64]

            # Se for bloco vazio, pula
            if not any(chunk_odd) and not any(chunk_even):
                continue

            tile_matrix = NeoGeoTileDecoder.decode_sprite_tile(chunk_odd, chunk_even)
            tile_img = self.render_tile_image(tile_matrix)

            col = i % cols
            row = i // cols
            sheet.paste(tile_img, (col * 16, row * 16))

        if scale > 1:
            sheet = sheet.resize((sheet_w * scale, sheet_h * scale), resample=Image.Resampling.NEAREST)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(output_path, "PNG")

        return sheet

    def extract_fix_sheet(
        self,
        output_path: Optional[Path] = None,
        cols: int = 32,
        scale: int = 2,
    ) -> Optional[Image.Image]:
        """Gera o atlas completo de fontes e HUD (Fix layer) a partir do S-ROM."""
        s_data = self.rom.get_s_rom_data()
        if not s_data:
            return None

        total_fix_tiles = len(s_data) // 32
        rows = (total_fix_tiles + cols - 1) // cols
        sheet_w = cols * 8
        sheet_h = rows * 8

        # Paleta limpa em tons de cinza/branco para fontes do HUD
        fix_palette = NeoGeoPalette.get_preset("grayscale")
        original_palette = self.palette
        self.palette = fix_palette

        sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

        for t in range(total_fix_tiles):
            chunk = s_data[t * 32 : (t + 1) * 32]
            if not any(chunk):
                continue
            matrix = NeoGeoTileDecoder.decode_fix_tile(chunk)
            tile_img = self.render_tile_image(matrix)

            col = t % cols
            row = t // cols
            sheet.paste(tile_img, (col * 8, row * 8))

        self.palette = original_palette

        if scale > 1:
            sheet = sheet.resize((sheet_w * scale, sheet_h * scale), resample=Image.Resampling.NEAREST)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(output_path, "PNG")

        return sheet

    def batch_extract_previews(
        self,
        output_dir: Path,
        tiles_per_sheet: int = 256,
        cols: int = 16,
        sheets_per_pair: int = 4,
    ) -> List[Path]:
        """Extrai folhas representativas de todos os pares de C-ROMs para exploração e auditoria."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files: List[Path] = []

        # 1. Extrai a camada Fix (HUD e Fontes)
        fix_path = output_dir / "fix_layer_hud_fonts.png"
        fix_img = self.extract_fix_sheet(output_path=fix_path, cols=32, scale=2)
        if fix_img:
            generated_files.append(fix_path)

        # 2. Extrai amostras de cada par de C-ROMs
        for c_pair in self.rom.c_pairs:
            pair_idx = c_pair.pair_index
            total_tiles = c_pair.pair_tiles

            # Calcula pontos equidistantes
            step = total_tiles // (sheets_per_pair + 1)
            for s in range(sheets_per_pair):
                start = max(1, s * step)
                out_file = output_dir / f"pair_{pair_idx}_tiles_{start:06d}_to_{start + tiles_per_sheet:06d}.png"
                self.extract_sheet(
                    pair_index=pair_idx,
                    start_tile=start,
                    count=tiles_per_sheet,
                    cols=cols,
                    output_path=out_file,
                )
                generated_files.append(out_file)

        return generated_files
