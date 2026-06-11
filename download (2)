from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .exceptions import ValidationError


class DataStore:
    """Persistencia simples em arquivo JSON."""

    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)

    def carregar(self) -> dict[str, Any]:
        if not self.caminho.exists():
            return {}
        try:
            with self.caminho.open("r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Arquivo de dados invalido: {self.caminho}") from exc
        if not isinstance(dados, dict):
            raise ValidationError("Arquivo de dados deve conter um objeto JSON.")
        return dados

    def salvar(self, dados: dict[str, Any]) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(self.caminho.suffix + ".tmp")
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        temporario.replace(self.caminho)
