#!/usr/bin/env python3
"""Script de automação para download, instalação e verificação das ferramentas JADX e JPEXS FFDec.

Permite configurar o ambiente de ferramentas em um único comando no Windows/Linux.
"""

import os
from pathlib import Path
import shutil
import sys
import urllib.request
import zipfile

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from ser_tools.core.config import SuiteConfig
from ser_tools.core.logger import get_console

JADX_VERSION = "1.5.0"
JADX_URL = f"https://github.com/skylot/jadx/releases/download/v{JADX_VERSION}/jadx-{JADX_VERSION}.zip"

FFDEC_VERSION = "26.3.0"
FFDEC_URL = f"https://github.com/jindrapetrik/jpexs-decompiler/releases/download/version{FFDEC_VERSION}/ffdec_{FFDEC_VERSION}.zip"


def install_tools(force: bool = False) -> int:
    console = get_console()
    config = SuiteConfig()
    tools_dir = config.tools_dir
    tools_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold cyan][*] Verificando ferramentas em:[/bold cyan] {tools_dir}")

    # 1. JADX
    jadx_dir = config.jadx_dir
    jadx_bin = config.jadx_bin
    if force or not jadx_bin or not jadx_bin.exists():
        console.print(f"[bold yellow][*] Baixando JADX v{JADX_VERSION}...[/bold yellow]")
        jadx_zip = tools_dir / "jadx_temp.zip"
        try:
            urllib.request.urlretrieve(JADX_URL, jadx_zip)
            if jadx_dir.exists():
                shutil.rmtree(jadx_dir, ignore_errors=True)
            jadx_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(jadx_zip, "r") as zf:
                zf.extractall(jadx_dir)
            console.print(f"[bold green][+] JADX instalado com sucesso em:[/bold green] {jadx_dir}")
        except Exception as e:
            console.print(f"[bold red][!] Falha ao baixar/instalar JADX: {e}[/bold red]")
        finally:
            if jadx_zip.exists():
                jadx_zip.unlink()
    else:
        console.print(f"[bold green][✓] JADX já instalado:[/bold green] {jadx_bin}")

    # 2. FFDec
    ffdec_dir = config.ffdec_dir
    ffdec_jar = config.ffdec_jar
    if force or not ffdec_jar.exists():
        console.print(f"[bold yellow][*] Baixando JPEXS FFDec v{FFDEC_VERSION}...[/bold yellow]")
        ffdec_zip = tools_dir / "ffdec_temp.zip"
        try:
            urllib.request.urlretrieve(FFDEC_URL, ffdec_zip)
            if ffdec_dir.exists():
                shutil.rmtree(ffdec_dir, ignore_errors=True)
            ffdec_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(ffdec_zip, "r") as zf:
                zf.extractall(ffdec_dir)
            console.print(f"[bold green][+] JPEXS FFDec instalado com sucesso em:[/bold green] {ffdec_dir}")
        except Exception as e:
            console.print(f"[bold red][!] Falha ao baixar/instalar FFDec: {e}[/bold red]")
        finally:
            if ffdec_zip.exists():
                ffdec_zip.unlink()
    else:
        console.print(f"[bold green][✓] JPEXS FFDec já instalado:[/bold green] {ffdec_jar}")

    # Diagnóstico pós-instalação
    config_after = SuiteConfig()
    env = config_after.detect_environment()
    console.print("\n[bold cyan]=== Diagnóstico Pós-Configuração ===[/bold cyan]")
    all_ok = True
    for key in ["python", "java", "jadx", "ffdec", "adb"]:
        st = env.get(key)
        if st and st.available:
            console.print(f" [bold green]✓[/bold green] {st.name}: {st.path or 'OK'}")
        else:
            console.print(f" [bold red]✗[/bold red] {key.upper()}: Ausente ou não configurado")
            all_ok = False

    return 0 if all_ok else 1


if __name__ == "__main__":
    force_reinstall = "--force" in sys.argv
    sys.exit(install_tools(force=force_reinstall))
