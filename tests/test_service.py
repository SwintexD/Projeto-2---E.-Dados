from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from atendimento.data_store import DataStore
from atendimento.exceptions import BusinessRuleError
from atendimento.service import AtendimentoService


class TestAtendimentoService(unittest.TestCase):
    def criar_service(self):
        diretorio = tempfile.TemporaryDirectory()
        caminho = Path(diretorio.name) / "dados.json"
        service = AtendimentoService(DataStore(caminho), carregar=True)
        self.addCleanup(diretorio.cleanup)
        return service

    def test_prioridade_e_fifo(self):
        service = self.criar_service()
        service.cadastrar_cliente(1, "Normal 1", "111", prioridade=False)
        service.cadastrar_cliente(2, "Prioritario 1", "222", prioridade=True)
        service.cadastrar_cliente(3, "Prioritario 2", "333", prioridade=True)
        service.cadastrar_atendente(1, "Atendente")

        service.abrir_atendimento(1)
        service.abrir_atendimento(2)
        service.abrir_atendimento(3)

        primeiro = service.chamar_proximo(1)
        self.assertEqual(primeiro.cliente_id, 2)
        service.finalizar_atendimento(1, duracao_minutos_manual=5)

        segundo = service.chamar_proximo(1)
        self.assertEqual(segundo.cliente_id, 3)
        service.finalizar_atendimento(1, duracao_minutos_manual=5)

        terceiro = service.chamar_proximo(1)
        self.assertEqual(terceiro.cliente_id, 1)

    def test_desfazer_ultima_finalizacao(self):
        service = self.criar_service()
        service.cadastrar_cliente(1, "Ana", "111", prioridade=False)
        service.cadastrar_atendente(1, "Carlos")
        service.abrir_atendimento(1)
        aberto = service.chamar_proximo(1)
        service.finalizar_atendimento(1, duracao_minutos_manual=12)

        self.assertEqual(len(service.historico), 1)
        restaurado = service.desfazer_ultima_finalizacao()
        self.assertEqual(restaurado.id, aberto.id)
        self.assertEqual(len(service.historico), 0)
        self.assertIn(aberto.id, service.atendimentos_abertos)

    def test_nao_remove_cliente_com_atendimento_aberto(self):
        service = self.criar_service()
        service.cadastrar_cliente(1, "Ana", "111", prioridade=False)
        service.cadastrar_atendente(1, "Carlos")
        service.abrir_atendimento(1)
        service.marcar_cliente_inativo(1)

        with self.assertRaises(BusinessRuleError):
            service.remover_clientes_inativos()

    def test_relatorio_top_e_csv(self):
        service = self.criar_service()
        service.cadastrar_cliente(1, "Ana", "111", prioridade=False)
        service.cadastrar_cliente(2, "Bruno", "222", prioridade=False)
        service.cadastrar_atendente(1, "Carlos")

        for cliente_id, duracao in [(1, 10), (2, 20), (1, 30)]:
            service.abrir_atendimento(cliente_id)
            service.chamar_proximo(1)
            service.finalizar_atendimento(1, duracao_minutos_manual=duracao)

        relatorio = service.relatorio_tempo_medio()
        self.assertEqual(relatorio["quantidade_atendimentos"], 3)
        self.assertEqual(relatorio["tempo_medio_minutos"], 20)
        self.assertEqual(service.top_5_clientes_mais_atendidos()[0]["cliente_id"], 1)

        with tempfile.TemporaryDirectory() as tmp:
            arquivos = service.exportar_relatorios_csv(tmp)
            self.assertEqual(len(arquivos), 4)
            self.assertTrue(all(arquivo.exists() for arquivo in arquivos))

    def test_vetor_temporario(self):
        service = self.criar_service()
        service.cadastrar_cliente_temporario(10, "Temp", "000", prioridade=True)
        self.assertEqual(len(service.clientes_temporarios), 1)
        service.efetivar_clientes_temporarios()
        self.assertIsNotNone(service.buscar_cliente_rapido(10, recursivo=True))


if __name__ == "__main__":
    unittest.main()
