from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from .exceptions import ValidationError


def agora_iso() -> str:
    """Retorna data/hora local em ISO sem microssegundos."""
    return datetime.now().replace(microsecond=0).isoformat()


def parse_data_iso(valor: str) -> datetime:
    try:
        return datetime.fromisoformat(valor)
    except ValueError as exc:
        raise ValidationError("Data invalida. Use o formato ISO: YYYY-MM-DDTHH:MM:SS.") from exc


def validar_id(valor: int, nome_campo: str) -> None:
    if not isinstance(valor, int) or valor <= 0:
        raise ValidationError(f"{nome_campo} deve ser um inteiro positivo.")


def validar_texto(valor: str, nome_campo: str) -> None:
    if not isinstance(valor, str) or not valor.strip():
        raise ValidationError(f"{nome_campo} nao pode ser vazio.")


@dataclass
class Cliente:
    id: int
    nome: str
    telefone: str
    prioridade: bool = False
    ativo: bool = True

    def validar(self) -> None:
        validar_id(self.id, "id do cliente")
        validar_texto(self.nome, "nome do cliente")
        validar_texto(self.telefone, "telefone do cliente")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> "Cliente":
        cliente = cls(
            id=int(dados["id"]),
            nome=str(dados["nome"]),
            telefone=str(dados["telefone"]),
            prioridade=bool(dados.get("prioridade", False)),
            ativo=bool(dados.get("ativo", True)),
        )
        cliente.validar()
        return cliente


@dataclass
class Atendente:
    id: int
    nome: str
    atendimento_atual_id: int | None = None

    @property
    def ocupado(self) -> bool:
        return self.atendimento_atual_id is not None

    def validar(self) -> None:
        validar_id(self.id, "id do atendente")
        validar_texto(self.nome, "nome do atendente")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> "Atendente":
        atual = dados.get("atendimento_atual_id")
        atendente = cls(
            id=int(dados["id"]),
            nome=str(dados["nome"]),
            atendimento_atual_id=int(atual) if atual is not None else None,
        )
        atendente.validar()
        return atendente


@dataclass
class AtendimentoFila:
    id: int
    cliente_id: int
    prioridade: bool
    entrada_fila: str

    def validar(self) -> None:
        validar_id(self.id, "id do atendimento")
        validar_id(self.cliente_id, "id do cliente")
        parse_data_iso(self.entrada_fila)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> "AtendimentoFila":
        item = cls(
            id=int(dados["id"]),
            cliente_id=int(dados["cliente_id"]),
            prioridade=bool(dados.get("prioridade", False)),
            entrada_fila=str(dados["entrada_fila"]),
        )
        item.validar()
        return item


@dataclass
class AtendimentoAberto:
    id: int
    cliente_id: int
    atendente_id: int
    prioridade: bool
    entrada_fila: str
    inicio_atendimento: str

    def validar(self) -> None:
        validar_id(self.id, "id do atendimento")
        validar_id(self.cliente_id, "id do cliente")
        validar_id(self.atendente_id, "id do atendente")
        parse_data_iso(self.entrada_fila)
        parse_data_iso(self.inicio_atendimento)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> "AtendimentoAberto":
        aberto = cls(
            id=int(dados["id"]),
            cliente_id=int(dados["cliente_id"]),
            atendente_id=int(dados["atendente_id"]),
            prioridade=bool(dados.get("prioridade", False)),
            entrada_fila=str(dados["entrada_fila"]),
            inicio_atendimento=str(dados["inicio_atendimento"]),
        )
        aberto.validar()
        return aberto


@dataclass
class HistoricoAtendimento:
    id: int
    cliente_id: int
    cliente_nome: str
    atendente_id: int
    atendente_nome: str
    data_inicio: str
    data_fim: str
    duracao_minutos: float
    espera_minutos: float

    def validar(self) -> None:
        validar_id(self.id, "id do historico")
        validar_id(self.cliente_id, "id do cliente")
        validar_texto(self.cliente_nome, "nome do cliente")
        validar_id(self.atendente_id, "id do atendente")
        validar_texto(self.atendente_nome, "nome do atendente")
        parse_data_iso(self.data_inicio)
        parse_data_iso(self.data_fim)
        if self.duracao_minutos < 0:
            raise ValidationError("Duracao nao pode ser negativa.")
        if self.espera_minutos < 0:
            raise ValidationError("Espera nao pode ser negativa.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> "HistoricoAtendimento":
        historico = cls(
            id=int(dados["id"]),
            cliente_id=int(dados["cliente_id"]),
            cliente_nome=str(dados["cliente_nome"]),
            atendente_id=int(dados["atendente_id"]),
            atendente_nome=str(dados["atendente_nome"]),
            data_inicio=str(dados["data_inicio"]),
            data_fim=str(dados["data_fim"]),
            duracao_minutos=float(dados["duracao_minutos"]),
            espera_minutos=float(dados.get("espera_minutos", 0.0)),
        )
        historico.validar()
        return historico
