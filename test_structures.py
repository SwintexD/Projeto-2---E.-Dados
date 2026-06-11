from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Iterable, Iterator

from .exceptions import BusinessRuleError
from .models import AtendimentoFila, Cliente


class FilaAtendimento:
    """Fila FIFO usada tanto para prioridade quanto para fila comum."""

    def __init__(self, itens: Iterable[AtendimentoFila] | None = None) -> None:
        self._itens: deque[AtendimentoFila] = deque(itens or [])

    def enfileirar(self, item: AtendimentoFila) -> None:
        self._itens.append(item)

    def desenfileirar(self) -> AtendimentoFila | None:
        if self.esta_vazia():
            return None
        return self._itens.popleft()

    def frente(self) -> AtendimentoFila | None:
        if self.esta_vazia():
            return None
        return self._itens[0]

    def esta_vazia(self) -> bool:
        return len(self._itens) == 0

    def contem_cliente(self, cliente_id: int) -> bool:
        return any(item.cliente_id == cliente_id for item in self._itens)

    def ids_clientes(self) -> set[int]:
        return {item.cliente_id for item in self._itens}

    def to_list(self) -> list[AtendimentoFila]:
        return list(self._itens)

    def __iter__(self) -> Iterator[AtendimentoFila]:
        return iter(self._itens)

    def __len__(self) -> int:
        return len(self._itens)


class PilhaDesfazer:
    """Pilha LIFO para desfazer a ultima finalizacao."""

    def __init__(self, itens: Iterable[dict[str, Any]] | None = None) -> None:
        self._itens: list[dict[str, Any]] = list(itens or [])

    def empilhar(self, acao: dict[str, Any]) -> None:
        self._itens.append(acao)

    def desempilhar(self) -> dict[str, Any] | None:
        if not self._itens:
            return None
        return self._itens.pop()

    def to_list(self) -> list[dict[str, Any]]:
        return list(self._itens)

    def __len__(self) -> int:
        return len(self._itens)


class VetorOrdenadoClientes:
    """Vetor ordenado por id com busca binaria."""

    def __init__(self, clientes: Iterable[Cliente] | None = None) -> None:
        self.atualizar(clientes or [])

    def atualizar(self, clientes: Iterable[Cliente]) -> None:
        self._clientes = sorted(clientes, key=lambda cliente: cliente.id)

    def buscar_por_id(self, cliente_id: int) -> Cliente | None:
        inicio = 0
        fim = len(self._clientes) - 1
        while inicio <= fim:
            meio = (inicio + fim) // 2
            cliente = self._clientes[meio]
            if cliente.id == cliente_id:
                return cliente
            if cliente.id < cliente_id:
                inicio = meio + 1
            else:
                fim = meio - 1
        return None

    def buscar_por_id_recursivo(self, cliente_id: int) -> Cliente | None:
        return self._buscar_recursivo(cliente_id, 0, len(self._clientes) - 1)

    def _buscar_recursivo(self, cliente_id: int, inicio: int, fim: int) -> Cliente | None:
        if inicio > fim:
            return None
        meio = (inicio + fim) // 2
        cliente = self._clientes[meio]
        if cliente.id == cliente_id:
            return cliente
        if cliente.id < cliente_id:
            return self._buscar_recursivo(cliente_id, meio + 1, fim)
        return self._buscar_recursivo(cliente_id, inicio, meio - 1)

    def to_list(self) -> list[Cliente]:
        return list(self._clientes)


@dataclass
class NoCliente:
    cliente_id: int
    proximo: "NoCliente | None" = None


class ListaEncadeadaClientes:
    """Lista encadeada simples para controlar clientes cadastrados."""

    def __init__(self) -> None:
        self.cabeca: NoCliente | None = None

    @classmethod
    def from_clientes(cls, clientes: Iterable[Cliente]) -> "ListaEncadeadaClientes":
        lista = cls()
        for cliente in clientes:
            lista.adicionar(cliente.id)
        return lista

    def adicionar(self, cliente_id: int) -> None:
        novo = NoCliente(cliente_id=cliente_id)
        if self.cabeca is None:
            self.cabeca = novo
            return
        atual = self.cabeca
        while atual.proximo is not None:
            atual = atual.proximo
        atual.proximo = novo

    def remover_inativos(
        self,
        clientes_por_id: dict[int, Cliente],
        clientes_bloqueados: set[int],
    ) -> list[int]:
        removidos: list[int] = []
        anterior: NoCliente | None = None
        atual = self.cabeca

        while atual is not None:
            cliente = clientes_por_id.get(atual.cliente_id)
            deve_remover = cliente is not None and not cliente.ativo
            if deve_remover and atual.cliente_id in clientes_bloqueados:
                raise BusinessRuleError(
                    "Nao e permitido remover cliente com atendimento em fila ou aberto."
                )
            if deve_remover:
                removidos.append(atual.cliente_id)
                if anterior is None:
                    self.cabeca = atual.proximo
                else:
                    anterior.proximo = atual.proximo
                atual = atual.proximo
            else:
                anterior = atual
                atual = atual.proximo
        return removidos

    def to_list(self) -> list[int]:
        ids: list[int] = []
        atual = self.cabeca
        while atual is not None:
            ids.append(atual.cliente_id)
            atual = atual.proximo
        return ids
