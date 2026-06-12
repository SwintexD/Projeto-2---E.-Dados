from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .cli import TerminalUI
from .data_store import DataStore
from .service import AtendimentoService


def configurar_logs(caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=caminho,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sistema de atendimento e analise")
    parser.add_argument(
        "--data",
        default="data/atendimento_data.json",
        help="Arquivo JSON de persistencia.",
    )
    parser.add_argument(
        "--log",
        default="logs/operacoes.log",
        help="Arquivo de logs.",
    )
    args = parser.parse_args()

    configurar_logs(Path(args.log))
    service = AtendimentoService(DataStore(args.data), carregar=True)
    TerminalUI(service).executar()
