#!/usr/bin/env python3
"""Script de automação para extração e catalogação visual dos sprites do KOF98.

Analisa o arquivo C:\\dev\\s_SER_Tools\\file\\kof98.zip, decodifica os barramentos C-ROM e S-ROM,
e gera sprite sheets em PNG de alta resolução junto com uma galeria visual HTML autocontida.
"""

from pathlib import Path
import sys
import time

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from ser_tools.core.logger import get_console, print_banner
from ser_tools.core.utils import format_bytes
from ser_tools.retro import NeoGeoPalette, NeoGeoRomPackage, NeoGeoSpriteExtractor


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
    # Seleção de ranges representativos em cada um dos 4 pares de C-ROMs
    targets = [
        # (Par, Início, Quantidade, Colunas, Nome, Descrição)
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

    # Também exporta uma versão em alto contraste forense do Boss/Efeitos para demonstrar a análise
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

    elapsed = time.time() - t0
    console.print(f"\n[bold green][✓] Extração finalizada com sucesso em {elapsed:.2f}s![/bold green]")

    # 3. Gera a Galeria Visual HTML
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

    <div class="gallery-grid">
        {"".join(cards_html)}
    </div>
</body>
</html>
"""
    html_path.write_text(html_content, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(extract_kof98())
