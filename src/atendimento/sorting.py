from __future__ import annotations

from typing import Callable, Iterable, TypeVar

T = TypeVar("T")


def merge_sort(
    itens: Iterable[T],
    key: Callable[[T], object] = lambda item: item,
    reverse: bool = False,
) -> list[T]:
    """Ordenacao merge sort recursiva, O(n log n)."""
    lista = list(itens)
    if len(lista) <= 1:
        return lista

    meio = len(lista) // 2
    esquerda = merge_sort(lista[:meio], key=key, reverse=reverse)
    direita = merge_sort(lista[meio:], key=key, reverse=reverse)
    return _intercalar(esquerda, direita, key, reverse)


def _intercalar(
    esquerda: list[T],
    direita: list[T],
    key: Callable[[T], object],
    reverse: bool,
) -> list[T]:
    resultado: list[T] = []
    i = 0
    j = 0

    while i < len(esquerda) and j < len(direita):
        chave_esq = key(esquerda[i])
        chave_dir = key(direita[j])
        if (chave_esq <= chave_dir and not reverse) or (chave_esq >= chave_dir and reverse):
            resultado.append(esquerda[i])
            i += 1
        else:
            resultado.append(direita[j])
            j += 1

    resultado.extend(esquerda[i:])
    resultado.extend(direita[j:])
    return resultado
