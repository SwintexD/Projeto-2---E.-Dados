from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from atendimento.models import AtendimentoFila, Cliente
from atendimento.structures import FilaAtendimento, VetorOrdenadoClientes


class TestEstruturas(unittest.TestCase):
    def test_busca_binaria_vetor_ordenado(self):
        vetor = VetorOrdenadoClientes(
            [
                Cliente(30, "C", "333"),
                Cliente(10, "A", "111"),
                Cliente(20, "B", "222"),
            ]
        )
        self.assertEqual(vetor.buscar_por_id(20).nome, "B")
        self.assertEqual(vetor.buscar_por_id_recursivo(10).nome, "A")
        self.assertIsNone(vetor.buscar_por_id(99))

    def test_fila_fifo(self):
        fila = FilaAtendimento()
        fila.enfileirar(AtendimentoFila(1, 100, False, "2026-01-01T10:00:00"))
        fila.enfileirar(AtendimentoFila(2, 200, False, "2026-01-01T10:01:00"))
        self.assertEqual(fila.desenfileirar().cliente_id, 100)
        self.assertEqual(fila.desenfileirar().cliente_id, 200)
        self.assertIsNone(fila.desenfileirar())


if __name__ == "__main__":
    unittest.main()
