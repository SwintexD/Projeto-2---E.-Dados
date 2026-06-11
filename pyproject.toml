from __future__ import annotations

from pathlib import Path

from .exceptions import AppError
from .service import AtendimentoService


class TerminalUI:
    def __init__(self, service: AtendimentoService) -> None:
        self.service = service

    def executar(self) -> None:
        while True:
            self._mostrar_menu()
            opcao = input("Escolha uma opcao: ").strip()
            try:
                if opcao == "0":
                    print("Saindo do sistema.")
                    return
                self._executar_opcao(opcao)
            except AppError as exc:
                print(f"Erro: {exc}")
            except ValueError:
                print("Erro: valor numerico invalido.")
            except KeyboardInterrupt:
                print("\nOperacao cancelada pelo usuario.")
                return

    def _mostrar_menu(self) -> None:
        print("\n=== Sistema de Atendimento ===")
        print("1  - Cadastrar cliente")
        print("2  - Cadastrar atendente")
        print("3  - Abrir atendimento")
        print("4  - Chamar proximo")
        print("5  - Finalizar atendimento")
        print("6  - Historico por cliente")
        print("7  - Desfazer ultima finalizacao")
        print("8  - Marcar cliente inativo")
        print("9  - Remover clientes inativos")
        print("10 - Relatorio de tempo medio")
        print("11 - Exportar relatorios CSV")
        print("12 - Busca rapida por cliente")
        print("13 - Top 5 clientes mais atendidos")
        print("14 - Alertas de espera alta")
        print("15 - Filtrar historico por data")
        print("16 - Cadastrar cliente temporario")
        print("17 - Efetivar cadastros temporarios")
        print("0  - Sair")

    def _executar_opcao(self, opcao: str) -> None:
        acoes = {
            "1": self._cadastrar_cliente,
            "2": self._cadastrar_atendente,
            "3": self._abrir_atendimento,
            "4": self._chamar_proximo,
            "5": self._finalizar_atendimento,
            "6": self._historico_por_cliente,
            "7": self._desfazer,
            "8": self._marcar_inativo,
            "9": self._remover_inativos,
            "10": self._relatorio_tempo_medio,
            "11": self._exportar_csv,
            "12": self._buscar_cliente,
            "13": self._top_clientes,
            "14": self._alertas,
            "15": self._filtrar_historico,
            "16": self._cadastrar_cliente_temporario,
            "17": self._efetivar_temporarios,
        }
        acao = acoes.get(opcao)
        if acao is None:
            print("Opcao invalida.")
            return
        acao()

    def _ler_int(self, mensagem: str) -> int:
        return int(input(mensagem).strip())

    def _ler_float_opcional(self, mensagem: str) -> float | None:
        valor = input(mensagem).strip()
        if not valor:
            return None
        return float(valor.replace(",", "."))

    def _ler_bool(self, mensagem: str) -> bool:
        valor = input(mensagem).strip().lower()
        return valor in {"s", "sim", "1", "true"}

    def _ler_filtro_data(self) -> tuple[str | None, str | None]:
        inicio = input("Data inicial (YYYY-MM-DD, vazio para ignorar): ").strip() or None
        fim = input("Data final (YYYY-MM-DD, vazio para ignorar): ").strip() or None
        return inicio, fim

    def _cadastrar_cliente(self) -> None:
        cliente = self.service.cadastrar_cliente(
            self._ler_int("Id do cliente: "),
            input("Nome: "),
            input("Telefone: "),
            self._ler_bool("Prioridade? (s/n): "),
        )
        print(f"Cliente cadastrado: {cliente.id} - {cliente.nome}")

    def _cadastrar_cliente_temporario(self) -> None:
        cliente = self.service.cadastrar_cliente_temporario(
            self._ler_int("Id do cliente temporario: "),
            input("Nome: "),
            input("Telefone: "),
            self._ler_bool("Prioridade? (s/n): "),
        )
        print(f"Cliente temporario cadastrado no vetor nao ordenado: {cliente.id}")

    def _efetivar_temporarios(self) -> None:
        efetivados = self.service.efetivar_clientes_temporarios()
        print(f"Clientes efetivados: {len(efetivados)}")

    def _cadastrar_atendente(self) -> None:
        atendente = self.service.cadastrar_atendente(
            self._ler_int("Id do atendente: "),
            input("Nome: "),
        )
        print(f"Atendente cadastrado: {atendente.id} - {atendente.nome}")

    def _abrir_atendimento(self) -> None:
        atendimento = self.service.abrir_atendimento(self._ler_int("Id do cliente: "))
        fila = "prioridade" if atendimento.prioridade else "comum"
        print(f"Atendimento {atendimento.id} entrou na fila {fila}.")

    def _chamar_proximo(self) -> None:
        atendimento = self.service.chamar_proximo(self._ler_int("Id do atendente: "))
        print(
            f"Atendimento {atendimento.id} chamado para o cliente "
            f"{atendimento.cliente_id}."
        )

    def _finalizar_atendimento(self) -> None:
        historico = self.service.finalizar_atendimento(
            self._ler_int("Id do atendente: "),
            self._ler_float_opcional(
                "Duracao manual em minutos (vazio para calcular automaticamente): "
            ),
        )
        print(
            f"Atendimento {historico.id} finalizado. "
            f"Duracao: {historico.duracao_minutos} min."
        )

    def _historico_por_cliente(self) -> None:
        cliente_id = self._ler_int("Id do cliente: ")
        inicio, fim = self._ler_filtro_data()
        historicos = self.service.historico_por_cliente(cliente_id, inicio, fim)
        self._imprimir_historico(historicos)

    def _desfazer(self) -> None:
        atendimento = self.service.desfazer_ultima_finalizacao()
        print(f"Finalizacao desfeita. Atendimento {atendimento.id} reaberto.")

    def _marcar_inativo(self) -> None:
        cliente = self.service.marcar_cliente_inativo(self._ler_int("Id do cliente: "))
        print(f"Cliente {cliente.id} marcado como inativo.")

    def _remover_inativos(self) -> None:
        removidos = self.service.remover_clientes_inativos()
        print(f"Clientes removidos: {removidos}")

    def _relatorio_tempo_medio(self) -> None:
        inicio, fim = self._ler_filtro_data()
        relatorio = self.service.relatorio_tempo_medio(inicio, fim)
        print(
            "Tempo medio: "
            f"{relatorio['tempo_medio_minutos']} min em "
            f"{relatorio['quantidade_atendimentos']} atendimento(s)."
        )

    def _exportar_csv(self) -> None:
        pasta = input("Pasta destino (padrao reports): ").strip() or "reports"
        inicio, fim = self._ler_filtro_data()
        arquivos = self.service.exportar_relatorios_csv(Path(pasta), inicio, fim)
        print("Arquivos gerados:")
        for arquivo in arquivos:
            print(f"- {arquivo}")

    def _buscar_cliente(self) -> None:
        cliente_id = self._ler_int("Id do cliente: ")
        recursivo = self._ler_bool("Usar busca binaria recursiva? (s/n): ")
        cliente = self.service.buscar_cliente_rapido(cliente_id, recursivo=recursivo)
        if cliente is None:
            print("Cliente nao encontrado.")
        else:
            print(
                f"Cliente encontrado: {cliente.id} - {cliente.nome} | "
                f"prioridade={cliente.prioridade} ativo={cliente.ativo}"
            )

    def _top_clientes(self) -> None:
        linhas = self.service.top_5_clientes_mais_atendidos()
        if not linhas:
            print("Nao ha historico para gerar ranking.")
            return
        for posicao, linha in enumerate(linhas, start=1):
            print(
                f"{posicao}. {linha['cliente_id']} - {linha['cliente_nome']}: "
                f"{linha['total_atendimentos']} atendimento(s)"
            )

    def _alertas(self) -> None:
        limite = self._ler_float_opcional("Limite em minutos (padrao 30): ")
        alertas = self.service.alertas_tempo_espera_alto(30.0 if limite is None else limite)
        if not alertas:
            print("Nenhum alerta de espera alta.")
            return
        for alerta in alertas:
            print(
                f"Atendimento {alerta['atendimento_id']} | "
                f"Cliente {alerta['cliente_id']} - {alerta['cliente_nome']} | "
                f"Fila {alerta['fila']} | Espera {alerta['espera_minutos']} min"
            )

    def _filtrar_historico(self) -> None:
        inicio, fim = self._ler_filtro_data()
        historicos = self.service.filtrar_historico_por_data(inicio, fim)
        self._imprimir_historico(historicos)

    def _imprimir_historico(self, historicos) -> None:
        if not historicos:
            print("Nenhum historico encontrado.")
            return
        for item in historicos:
            print(
                f"Atendimento {item.id} | Cliente {item.cliente_id} - {item.cliente_nome} | "
                f"Atendente {item.atendente_id} - {item.atendente_nome} | "
                f"Fim {item.data_fim} | Duracao {item.duracao_minutos} min"
            )
