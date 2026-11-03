#!/usr/bin/env python3
"""Script de automação para auditoria estática e análise de vulnerabilidades rápida.

Uso:
    python scripts/quick_audit.py <caminho_ou_pacote> [--format all|json|md|html]
"""

import argparse
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from ser_tools.audit.suite_auditor import SuiteAuditor
from ser_tools.core.config import SuiteConfig
from ser_tools.core.logger import get_console, print_banner


def run_quick_audit(target: str, export_format: str = "all", output_dest: str = None) -> int:
    console = get_console()
    config = SuiteConfig()
    auditor = SuiteAuditor(config)

    print_banner()
    console.print(f"[bold cyan][*] Iniciando auditoria rápida no alvo:[/bold cyan] {target}")

    try:
        report = auditor.audit_target(target)
    except Exception as e:
        console.print(f"[bold red][!] Falha ao auditar alvo '{target}': {e}[/bold red]")
        return 1

    summary = report.get_summary()
    score_info = report.calculate_risk_score()

    console.print(f"\n[bold green]Auditoria concluída com sucesso![/bold green]")
    console.print(f"Alvo: [cyan]{report.target_name}[/cyan] (Tipo: {report.target_type})")
    console.print(f"Classificação de Risco: [bold yellow]{score_info['grade']}[/bold yellow] (Score: {score_info['score']}/100)")
    console.print(f"Vulnerabilidades Encontradas: {len(report.findings)}")
    console.print(
        f"  - Críticas: [red]{summary.get('CRITICAL', 0)}[/red] | "
        f"Altas: [yellow]{summary.get('HIGH', 0)}[/yellow] | "
        f"Médias: {summary.get('MEDIUM', 0)} | "
        f"Baixas: {summary.get('LOW', 0)} | "
        f"Informativas: {summary.get('INFO', 0)}"
    )

    # Exportação
    if output_dest:
        dest_base = Path(output_dest)
    else:
        dest_base = config.reports_dir / f"audit_{report.target_name}"

    if export_format in ("json", "all"):
        json_file = dest_base.with_suffix(".json") if dest_base.suffix == ".json" else dest_base.parent / f"{dest_base.name}.json"
        report.export_json(json_file)
        console.print(f"[+] Relatório JSON: {json_file}")

    if export_format in ("md", "all"):
        md_file = dest_base.with_suffix(".md") if dest_base.suffix == ".md" else dest_base.parent / f"{dest_base.name}.md"
        report.export_markdown(md_file)
        console.print(f"[+] Relatório Markdown: {md_file}")

    if export_format in ("html", "all"):
        html_file = dest_base.with_suffix(".html") if dest_base.suffix == ".html" else dest_base.parent / f"{dest_base.name}.html"
        report.export_html(html_file)
        console.print(f"[+] Relatório HTML: {html_file}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditoria Rápida s_SER_Tools")
    parser.add_argument("target", help="Caminho do arquivo, pasta ou nome de pacote a auditar")
    parser.add_argument("--format", "-f", choices=["all", "json", "md", "html"], default="all", help="Formato de relatório")
    parser.add_argument("--output", "-o", help="Caminho base de saída para os relatórios")
    args = parser.parse_args()

    return run_quick_audit(args.target, export_format=args.format, output_dest=args.output)


if __name__ == "__main__":
    sys.exit(main())
