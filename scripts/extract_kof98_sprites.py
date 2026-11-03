#!/usr/bin/env python3
"""Script de automação para extração e catalogação visual dos sprites e animações do KOF98.

Analisa o arquivo C:\\dev\\s_SER_Tools\\file\\kof98.zip, decodifica os barramentos C-ROM e S-ROM,
e gera sprite sheets em PNG, GIFs animados da abertura/combate e uma galeria visual HTML autocontida.
"""

from pathlib import Path
import sys
import time

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from PIL import Image, ImageDraw
from ser_tools.core.logger import get_console, print_banner
from ser_tools.core.utils import format_bytes
from ser_tools.retro import NeoGeoPalette, NeoGeoRomPackage, NeoGeoSpriteExtractor, NeoGeoTileDecoder


def generate_animated_gifs(pkg: NeoGeoRomPackage, out_dir: Path, console):
    """Gera animações em GIF da abertura arcade, combate e efeitos de chamas."""
    console.print("\n[bold cyan][*] Gerando animações em GIF da Abertura e Lutadores...[/bold cyan]")
    c1, c2 = pkg.get_c_pair_data(1)
    pal_arcade = NeoGeoPalette.get_preset("arcade_p1")

    # 1. Fighter Stance / Intro Loop (Tiles 512..1024, 24 frames, 4x8 tiles cada = 64x128 -> 128x256)
    fighter_frames = []
    scale = 2
    for f in range(24):
        start_t = 512 + f * 32
        im = Image.new("RGBA", (4 * 16, 8 * 16), (0, 0, 0, 0))
        for c in range(4):
            for r in range(8):
                t = start_t + (c * 8 + r)
                tile_m = NeoGeoTileDecoder.decode_sprite_tile(c1[t * 64 : (t + 1) * 64], c2[t * 64 : (t + 1) * 64])
                for y in range(16):
                    for x in range(16):
                        im.putpixel((c * 16 + x, r * 16 + y), pal_arcade[tile_m[y, x]])
        if scale > 1:
            im = im.resize((4 * 16 * scale, 8 * 16 * scale), resample=Image.Resampling.NEAREST)
        fighter_frames.append(im)

    gif_fighter = out_dir / "kof98_fighter_intro_anim.gif"
    fighter_frames[0].save(
        gif_fighter,
        save_all=True,
        append_images=fighter_frames[1:],
        duration=100,
        loop=0,
        disposal=2,
    )
    console.print(f"  [green]✓[/green] Animação de Combate -> [cyan]{gif_fighter.name}[/cyan] (24 frames)")

    # 2. Kyo Kusanagi Flame Intro (Tiles 10000..10512, 16 frames, 4x8 tiles cada)
    kyo_frames = []
    for f in range(16):
        start_t = 10000 + f * 32
        im = Image.new("RGBA", (4 * 16, 8 * 16), (0, 0, 0, 0))
        for c in range(4):
            for r in range(8):
                t = start_t + (c * 8 + r)
                tile_m = NeoGeoTileDecoder.decode_sprite_tile(c1[t * 64 : (t + 1) * 64], c2[t * 64 : (t + 1) * 64])
                for y in range(16):
                    for x in range(16):
                        im.putpixel((c * 16 + x, r * 16 + y), pal_arcade[tile_m[y, x]])
        if scale > 1:
            im = im.resize((4 * 16 * scale, 8 * 16 * scale), resample=Image.Resampling.NEAREST)
        kyo_frames.append(im)

    gif_kyo = out_dir / "kof98_kyo_flame_intro.gif"
    kyo_frames[0].save(
        gif_kyo,
        save_all=True,
        append_images=kyo_frames[1:],
        duration=100,
        loop=0,
        disposal=2,
    )
    console.print(f"  [green]✓[/green] Kyo Kusanagi Chamas -> [cyan]{gif_kyo.name}[/cyan] (16 frames)")

    # 3. Abertura Arcade Completa (320x224 com logo do KOF98 e lutador animado)
    title_banner = Image.new("RGBA", (13 * 16, 12 * 16), (0, 0, 0, 0))
    for c in range(13):
        for r in range(12):
            t = 128 + (r * 13 + c)
            tile_m = NeoGeoTileDecoder.decode_sprite_tile(c1[t * 64 : (t + 1) * 64], c2[t * 64 : (t + 1) * 64])
            for y in range(16):
                for x in range(16):
                    title_banner.putpixel((c * 16 + x, r * 16 + y), pal_arcade[tile_m[y, x]])

    arcade_w = 320
    arcade_h = 224
    composite_frames = []
    banner_scaled = title_banner.resize((156, 144), resample=Image.Resampling.NEAREST)

    for f_im in fighter_frames[:16]:
        canvas = Image.new("RGBA", (arcade_w, arcade_h), (8, 12, 18, 255))
        draw = ImageDraw.Draw(canvas)
        for y in range(0, arcade_h, 2):
            draw.line([(0, y), (arcade_w, y)], fill=(4, 6, 10, 80))

        canvas.paste(banner_scaled, (10, 35), banner_scaled)
        # Sombra no chão
        fighter_x, fighter_y = 190, 65
        draw.ellipse([fighter_x + 8, fighter_y + 120, fighter_x + 56, fighter_y + 132], fill=(2, 4, 8, 180))
        # Lutador em escala original 1x (64x128)
        f_small = f_im.resize((64, 128), resample=Image.Resampling.NEAREST)
        canvas.paste(f_small, (fighter_x, fighter_y), f_small)
        draw.rectangle([0, 0, arcade_w - 1, arcade_h - 1], outline=(48, 54, 61, 255), width=2)
        composite_frames.append(canvas)

    gif_opening = out_dir / "kof98_opening_arcade_intro.gif"
    composite_frames[0].save(
        gif_opening,
        save_all=True,
        append_images=composite_frames[1:],
        duration=110,
        loop=0,
    )
    console.print(f"  [green]✓[/green] Abertura Arcade Completa -> [cyan]{gif_opening.name}[/cyan] (320x224, 16 frames)")


def extract_kof98():
    console = get_console()
    print_banner()

    zip_path = repo_root / "file" / "kof98.zip"
    out_dir = repo_root / "file" / "extracted_sprites"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not zip_path.is_file():
        console.print(f"[bold red][!] Arquivo kof98.zip não encontrado em: {zip_path}[/bold red]")
        return 1

    console.print(f"[bold cyan][*] Carregando e inspecionando ROM Arcade:[/bold cyan] {zip_path}")
    pkg = NeoGeoRomPackage(zip_path)
    info = pkg.inspect()

    console.print(f"[bold green][✓] Pacote Neo Geo Reconhecido:[/bold green] {info['archive_name']} ({format_bytes(info['archive_size_bytes'])})")
    console.print(f"    - Pares de C-ROM (Sprites 16x16): [cyan]{info['total_c_pairs']} pares[/cyan] ({info['total_sprite_tiles']:,} tiles = {format_bytes(info['total_sprite_bytes'])})")
    console.print(f"    - Fix Layer (Texto/HUD 8x8): [cyan]{info['fix_rom']}[/cyan] ({info['fix_tiles']:,} tiles)")
    console.print(f"    - Program ROMs (68k): [yellow]{len(info['program_roms'])} arquivos[/yellow] ({', '.join(info['program_roms'])})")
    console.print(f"    - Sound ROMs: [yellow]Z80 ({info['sound_roms']['m_rom']}) + {len(info['sound_roms']['v_roms'])} ADPCM banks[/yellow]")

    extractor = NeoGeoSpriteExtractor(pkg)

    # 1. Extrai a camada Fix (HUD e Fontes)
    console.print("\n[bold cyan][*] Decodificando Camada Fix (HUD, fontes, numerais e ícones 8x8)...[/bold cyan]")
    fix_out = out_dir / "kof98_fix_hud_fonts.png"
    extractor.extract_fix_sheet(output_path=fix_out, cols=32, scale=2)
    console.print(f"[bold green][✓] Fix Layer exportada para:[/bold green] {fix_out}")

    # 2. Extrai folhas de sprites estratégicas (Intros, Telas de Título, Golpes e Lutadores)
    targets = [
        (1, 1, 512, 16, "pair1_intro_title_tiles.png", "Abertura, SNK Logo e Telas de Título"),
        (1, 2000, 512, 16, "pair1_fighter_portraits_select.png", "Retratos dos Lutadores e Seleção"),
        (1, 10000, 512, 16, "pair1_character_anim_kusanagi.png", "Animações de Combate (Kyo Kusanagi & Iori Team)"),
        (1, 40000, 512, 16, "pair1_character_anim_fatal_fury.png", "Animações de Combate (Terry, Andy & Joe Team)"),
        (2, 500, 512, 16, "pair2_character_anim_art_of_fighting.png", "Equipe Art of Fighting (Ryo, Robert, Takuma)"),
        (2, 25000, 512, 16, "pair2_character_anim_ikari_team.png", "Equipe Ikari Warriors (Leona, Ralf, Clark)"),
        (3, 1000, 512, 16, "pair3_character_anim_psycho_soldier.png", "Equipe Psycho Soldier (Athena, Kensou, Chin)"),
        (3, 30000, 512, 16, "pair3_character_anim_womens_team.png", "Equipe Feminina (Mai, King, Chizuru)"),
        (4, 1500, 512, 16, "pair4_character_anim_korea_team.png", "Equipe Coreia (Kim, Chang, Choi)"),
        (4, 25000, 512, 16, "pair4_boss_rugal_omega_special.png", "Boss Omega Rugal e Efeitos Especiais (SDks/Super)"),
    ]

    console.print("\n[bold cyan][*] Decodificando folhas de sprites (16x16 4BPP planar LSPC)...[/bold cyan]")
    t0 = time.time()
    extracted_sheets = []

    for pair_idx, start, count, cols, fname, desc in targets:
        out_sheet = out_dir / fname
        extractor.set_palette("arcade_p1")
        extractor.extract_sheet(
            pair_index=pair_idx,
            start_tile=start,
            count=count,
            cols=cols,
            output_path=out_sheet,
            scale=1,
        )
        extracted_sheets.append((fname, desc, pair_idx, start, count))
        console.print(f"  [green]✓[/green] Par {pair_idx} | Tiles {start:05d}..{start+count:05d} -> [cyan]{fname}[/cyan] ({desc})")

    # Versão em alto contraste forense do Boss/Efeitos
    contrast_sheet = out_dir / "pair4_boss_rugal_high_contrast_forensic.png"
    extractor.set_palette("contrast")
    extractor.extract_sheet(
        pair_index=4,
        start_tile=25000,
        count=512,
        cols=16,
        output_path=contrast_sheet,
        scale=1,
    )
    extracted_sheets.append(("pair4_boss_rugal_high_contrast_forensic.png", "Análise Forense de Bitplanes (Alto Contraste)", 4, 25000, 512))
    console.print(f"  [green]✓[/green] Par 4 | Análise Forense de Bitplanes -> [cyan]{contrast_sheet.name}[/cyan]")

    # 3. Gera Animações em GIF
    generate_animated_gifs(pkg, out_dir, console)

    elapsed = time.time() - t0
    console.print(f"\n[bold green][✓] Extração e animações finalizadas com sucesso em {elapsed:.2f}s![/bold green]")

    # 4. Gera a Galeria Visual HTML
    html_file = out_dir / "index.html"
    generate_html_gallery(html_file, info, extracted_sheets, fix_out.name)
    console.print(f"[bold green][✓] Galeria visual interativa gerada em:[/bold green] {html_file}")

    return 0


def generate_html_gallery(html_path: Path, rom_info: dict, sheets: list, fix_fname: str):
    """Gera um visualizador HTML moderno com tema dark arcade para inspeção dos sprites."""
    cards_html = []

    # Card Fix Layer
    cards_html.append(f"""
        <div class="card">
            <div class="card-header">
                <h3>Camada Fix (S-ROM: {rom_info['fix_rom']})</h3>
                <span class="badge">4.096 Tiles 8x8 (HUD & Fontes)</span>
            </div>
            <div class="img-container">
                <img src="{fix_fname}" alt="Fix Layer">
            </div>
            <p class="desc">Textos do sistema, fontes de diálogo, contador de tempo, barra de energia e logos de vitória.</p>
        </div>
    """)

    for fname, desc, pair, start, count in sheets:
        cards_html.append(f"""
        <div class="card">
            <div class="card-header">
                <h3>{desc}</h3>
                <span class="badge">C-ROM Par {pair} | Tiles #{start:,} - #{start+count:,}</span>
            </div>
            <div class="img-container">
                <img src="{fname}" alt="{desc}">
            </div>
            <p class="desc">Arquivo gerado: <code>{fname}</code> (Grade 16 colunas &times; 16px, 4BPP planar).</p>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Galeria de Sprites KOF '98 - s_SER_Tools</title>
    <style>
        :root {{
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --accent: #58a6ff;
            --accent-gold: #f1e05a;
            --text: #c9d1d9;
            --text-title: #f0f6fc;
        }}
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 24px;
        }}
        header {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        h1 {{
            color: var(--text-title);
            margin: 0 0 8px 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .kof-tag {{
            background: #da3633;
            color: white;
            font-size: 14px;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: bold;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin-top: 16px;
        }}
        .meta-item {{
            background: #090d13;
            padding: 10px 14px;
            border-radius: 6px;
            border: 1px solid var(--border);
        }}
        .meta-label {{
            font-size: 12px;
            color: #8b949e;
            text-transform: uppercase;
        }}
        .meta-val {{
            font-size: 15px;
            font-weight: 600;
            color: var(--text-title);
            margin-top: 4px;
        }}
        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        .card-header {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .card-header h3 {{
            margin: 0;
            font-size: 15px;
            color: var(--text-title);
        }}
        .badge {{
            background: #1f6feb;
            color: white;
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 12px;
        }}
        .img-container {{
            background: #05070a;
            background-image: 
                linear-gradient(45deg, #0e131b 25%, transparent 25%), 
                linear-gradient(-45deg, #0e131b 25%, transparent 25%), 
                linear-gradient(45deg, transparent 75%, #0e131b 75%), 
                linear-gradient(-45deg, transparent 75%, #0e131b 75%);
            background-size: 16px 16px;
            background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 280px;
        }}
        .img-container img {{
            image-rendering: pixelated;
            max-width: 100%;
            height: auto;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            transition: transform 0.2s ease;
        }}
        .img-container img:hover {{
            transform: scale(1.4);
            cursor: zoom-in;
            z-index: 10;
        }}
        .desc {{
            padding: 12px 16px;
            font-size: 13px;
            color: #8b949e;
            margin: 0;
        }}
        code {{
            background: rgba(110,118,129,0.2);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            color: #f0883e;
        }}
    </style>
</head>
<body>
    <header>
        <h1>
            <span>SNK Neo Geo Arcade — The King of Fighters '98</span>
            <span class="kof-tag">KOF '98</span>
        </h1>
        <p>Sprite Sheets e Camada Gráfica LSPC extraídos via <code>s_SER_Tools v3.0</code> (Módulo Retro & Arcade).</p>
        <div class="meta-grid">
            <div class="meta-item">
                <div class="meta-label">Total de Sprites 16x16</div>
                <div class="meta-val">{rom_info['total_sprite_tiles']:,} tiles</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Memória C-ROM</div>
                <div class="meta-val">{format_bytes(rom_info['total_sprite_bytes'])} (8 ROMs)</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Camada Fix (HUD)</div>
                <div class="meta-val">{rom_info['fix_tiles']:,} tiles (8x8)</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Formato do Barramento</div>
                <div class="meta-val">4BPP Planar Intercalado LSPC</div>
            </div>
        </div>
    </header>

    <!-- SEÇÃO DE ANIMAÇÕES EM GIF -->
    <section style="background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 24px; margin-bottom: 24px;">
        <h2 style="color: var(--text-title); margin: 0 0 16px 0; display: flex; align-items: center; gap: 10px;">
            <span>🎬 Animações da Abertura & Lutadores em GIF</span>
            <span style="background: #238636; color: white; font-size: 12px; padding: 2px 8px; border-radius: 12px;">ATIVO</span>
        </h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
            <div style="background: #090d13; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; text-align: center;">
                <div style="padding: 12px; font-weight: bold; color: var(--text-title); border-bottom: 1px solid var(--border);">
                    Abertura Arcade Completa (320x224)
                </div>
                <div style="padding: 16px; min-height: 240px; display: flex; align-items: center; justify-content: center;">
                    <img src="kof98_opening_arcade_intro.gif" style="max-width: 100%; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.6);" alt="Abertura Arcade KOF 98">
                </div>
                <div style="padding: 10px; font-size: 12px; color: #8b949e; border-top: 1px solid var(--border);">
                    <code>kof98_opening_arcade_intro.gif</code> (16 frames)
                </div>
            </div>

            <div style="background: #090d13; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; text-align: center;">
                <div style="padding: 12px; font-weight: bold; color: var(--text-title); border-bottom: 1px solid var(--border);">
                    Animação de Combate / Stance Loop
                </div>
                <div style="padding: 16px; min-height: 240px; display: flex; align-items: center; justify-content: center;">
                    <img src="kof98_fighter_intro_anim.gif" style="max-height: 230px; image-rendering: pixelated; box-shadow: 0 4px 12px rgba(0,0,0,0.6);" alt="Lutador Stance Loop">
                </div>
                <div style="padding: 10px; font-size: 12px; color: #8b949e; border-top: 1px solid var(--border);">
                    <code>kof98_fighter_intro_anim.gif</code> (24 frames)
                </div>
            </div>

            <div style="background: #090d13; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; text-align: center;">
                <div style="padding: 12px; font-weight: bold; color: var(--text-title); border-bottom: 1px solid var(--border);">
                    Kyo Kusanagi Chamas / Special Intro
                </div>
                <div style="padding: 16px; min-height: 240px; display: flex; align-items: center; justify-content: center;">
                    <img src="kof98_kyo_flame_intro.gif" style="max-height: 230px; image-rendering: pixelated; box-shadow: 0 4px 12px rgba(0,0,0,0.6);" alt="Kyo Kusanagi Flames">
                </div>
                <div style="padding: 10px; font-size: 12px; color: #8b949e; border-top: 1px solid var(--border);">
                    <code>kof98_kyo_flame_intro.gif</code> (16 frames)
                </div>
            </div>
        </div>
    </section>

    <div class="gallery-grid">
        {"".join(cards_html)}
    </div>
</body>
</html>
"""
    html_path.write_text(html_content, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(extract_kof98())
