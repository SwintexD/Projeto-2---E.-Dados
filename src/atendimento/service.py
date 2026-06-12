from __future__ import annotations

import csv
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .data_store import DataStore
from .exceptions import BusinessRuleError, NotFoundError, ValidationError
from .models import (
    AtendimentoAberto,
    AtendimentoFila,
    Atendente,
    Cliente,
    HistoricoAtendimento,
    agora_iso,
    parse_data_iso,
)
from .sorting import merge_sort
from .structures import (
    FilaAtendimento,
    ListaEncadeadaClientes,
    PilhaDesfazer,
    VetorOrdenadoClientes,
)

logger = logging.getLogger(__name__)


class AtendimentoService:
    """Camada de regras de negocio do sistema."""

    def __init__(self, store: DataStore | None = None, carregar: bool = True) -> None:
        self.store = store
        self.clientes: dict[int, Cliente] = {}
        self.atendentes: dict[int, Atendente] = {}
        self.fila_prioridade = FilaAtendimento()
        self.fila_comum = FilaAtendimento()
        self.atendimentos_abertos: dict[int, AtendimentoAberto] = {}
        self.historico: list[HistoricoAtendimento] = []
        self.pilha_desfazer = PilhaDesfazer()
        self.clientes_temporarios: list[Cliente] = []
        self.proximo_atendimento_id = 1
        self.indice_clientes = VetorOrdenadoClientes()
        self.lista_clientes = ListaEncadeadaClientes()

        if carregar and self.store is not None:
            self._carregar()

    def _carregar(self) -> None:
        dados = self.store.carregar() if self.store else {}
        if not dados:
            return

        self.proximo_atendimento_id = int(dados.get("proximo_atendimento_id", 1))
        self.clientes = {
            cliente.id: cliente
            for cliente in (Cliente.from_dict(item) for item in dados.get("clientes", []))
        }
        self.atendentes = {
            atendente.id: atendente
            for atendente in (
                Atendente.from_dict(item) for item in dados.get("atendentes", [])
            )
        }
        self.fila_prioridade = FilaAtendimento(
            AtendimentoFila.from_dict(item) for item in dados.get("fila_prioridade", [])
        )
        self.fila_comum = FilaAtendimento(
            AtendimentoFila.from_dict(item) for item in dados.get("fila_comum", [])
        )
        self.atendimentos_abertos = {
            aberto.id: aberto
            for aberto in (
                AtendimentoAberto.from_dict(item)
                for item in dados.get("atendimentos_abertos", [])
            )
        }
        self.historico = [
            HistoricoAtendimento.from_dict(item) for item in dados.get("historico", [])
        ]
        self.pilha_desfazer = PilhaDesfazer(dados.get("pilha_desfazer", []))
        self.clientes_temporarios = [
            Cliente.from_dict(item) for item in dados.get("clientes_temporarios", [])
        ]
        self._reconstruir_indices()

    def _salvar(self) -> None:
        if self.store is not None:
            self.store.salvar(self._to_dict())

    def _to_dict(self) -> dict[str, Any]:
        return {
            "proximo_atendimento_id": self.proximo_atendimento_id,
            "clientes": [cliente.to_dict() for cliente in self.clientes.values()],
            "atendentes": [atendente.to_dict() for atendente in self.atendentes.values()],
            "fila_prioridade": [item.to_dict() for item in self.fila_prioridade],
            "fila_comum": [item.to_dict() for item in self.fila_comum],
            "atendimentos_abertos": [
                aberto.to_dict() for aberto in self.atendimentos_abertos.values()
            ],
            "historico": [item.to_dict() for item in self.historico],
            "pilha_desfazer": self.pilha_desfazer.to_list(),
            "clientes_temporarios": [
                cliente.to_dict() for cliente in self.clientes_temporarios
            ],
        }

    def _reconstruir_indices(self) -> None:
        self.indice_clientes.atualizar(self.clientes.values())
        self.lista_clientes = ListaEncadeadaClientes.from_clientes(self.clientes.values())

    def _obter_cliente(self, cliente_id: int) -> Cliente:
        cliente = self.clientes.get(cliente_id)
        if cliente is None:
            raise NotFoundError("Cliente nao encontrado.")
        return cliente

    def _obter_atendente(self, atendente_id: int) -> Atendente:
        atendente = self.atendentes.get(atendente_id)
        if atendente is None:
            raise NotFoundError("Atendente nao encontrado.")
        return atendente

    def cadastrar_cliente(
        self,
        cliente_id: int,
        nome: str,
        telefone: str,
        prioridade: bool = False,
    ) -> Cliente:
        if cliente_id in self.clientes:
            raise BusinessRuleError("Ja existe cliente com esse id.")
        cliente = Cliente(cliente_id, nome.strip(), telefone.strip(), prioridade, True)
        cliente.validar()
        self.clientes[cliente.id] = cliente
        self.lista_clientes.adicionar(cliente.id)
        self.indice_clientes.atualizar(self.clientes.values())
        self._salvar()
        logger.info("Cliente cadastrado: id=%s nome=%s", cliente.id, cliente.nome)
        return cliente

    def cadastrar_cliente_temporario(
        self,
        cliente_id: int,
        nome: str,
        telefone: str,
        prioridade: bool = False,
    ) -> Cliente:
        if cliente_id in self.clientes:
            raise BusinessRuleError("Cliente ja existe no cadastro definitivo.")
        if any(cliente.id == cliente_id for cliente in self.clientes_temporarios):
            raise BusinessRuleError("Cliente ja existe no vetor temporario.")
        cliente = Cliente(cliente_id, nome.strip(), telefone.strip(), prioridade, True)
        cliente.validar()
        self.clientes_temporarios.append(cliente)
        self._salvar()
        logger.info("Cliente temporario cadastrado: id=%s", cliente.id)
        return cliente

    def efetivar_clientes_temporarios(self) -> list[Cliente]:
        for cliente in self.clientes_temporarios:
            if cliente.id in self.clientes:
                raise BusinessRuleError(
                    f"Cliente temporario {cliente.id} conflita com cadastro existente."
                )
        efetivados = list(self.clientes_temporarios)
        for cliente in efetivados:
            self.clientes[cliente.id] = cliente
            self.lista_clientes.adicionar(cliente.id)
        self.clientes_temporarios.clear()
        self.indice_clientes.atualizar(self.clientes.values())
        self._salvar()
        logger.info("Clientes temporarios efetivados: total=%s", len(efetivados))
        return efetivados

    def cadastrar_atendente(self, atendente_id: int, nome: str) -> Atendente:
        if atendente_id in self.atendentes:
            raise BusinessRuleError("Ja existe atendente com esse id.")
        atendente = Atendente(atendente_id, nome.strip())
        atendente.validar()
        self.atendentes[atendente.id] = atendente
        self._salvar()
        logger.info("Atendente cadastrado: id=%s nome=%s", atendente.id, atendente.nome)
        return atendente

    def abrir_atendimento(self, cliente_id: int) -> AtendimentoFila:
        cliente = self._obter_cliente(cliente_id)
        if not cliente.ativo:
            raise BusinessRuleError("Cliente inativo nao pode abrir atendimento.")
        if self._cliente_tem_atendimento_em_andamento(cliente_id):
            raise BusinessRuleError("Cliente ja possui atendimento em fila ou aberto.")

        item = AtendimentoFila(
            id=self.proximo_atendimento_id,
            cliente_id=cliente.id,
            prioridade=cliente.prioridade,
            entrada_fila=agora_iso(),
        )
        self.proximo_atendimento_id += 1
        if item.prioridade:
            self.fila_prioridade.enfileirar(item)
        else:
            self.fila_comum.enfileirar(item)
        self._salvar()
        logger.info("Atendimento aberto: atendimento=%s cliente=%s", item.id, cliente.id)
        return item

    def chamar_proximo(self, atendente_id: int) -> AtendimentoAberto:
        atendente = self._obter_atendente(atendente_id)
        if atendente.ocupado:
            raise BusinessRuleError("Atendente ja esta em atendimento.")

        item = self.fila_prioridade.desenfileirar()
        if item is None:
            item = self.fila_comum.desenfileirar()
        if item is None:
            raise BusinessRuleError("Nao ha clientes na fila.")

        aberto = AtendimentoAberto(
            id=item.id,
            cliente_id=item.cliente_id,
            atendente_id=atendente.id,
            prioridade=item.prioridade,
            entrada_fila=item.entrada_fila,
            inicio_atendimento=agora_iso(),
        )
        atendente.atendimento_atual_id = aberto.id
        self.atendimentos_abertos[aberto.id] = aberto
        self._salvar()
        logger.info(
            "Atendimento chamado: atendimento=%s atendente=%s cliente=%s",
            aberto.id,
            atendente.id,
            aberto.cliente_id,
        )
        return aberto

    def finalizar_atendimento(
        self,
        atendente_id: int,
        duracao_minutos_manual: float | None = None,
        data_fim: str | None = None,
    ) -> HistoricoAtendimento:
        atendente = self._obter_atendente(atendente_id)
        if atendente.atendimento_atual_id is None:
            raise BusinessRuleError("Nao ha atendimento aberto para esse atendente.")

        aberto = self.atendimentos_abertos.get(atendente.atendimento_atual_id)
        if aberto is None:
            raise BusinessRuleError("Atendimento do atendente nao foi encontrado.")

        cliente = self._obter_cliente(aberto.cliente_id)
        fim = parse_data_iso(data_fim) if data_fim else datetime.now().replace(microsecond=0)
        inicio = parse_data_iso(aberto.inicio_atendimento)
        entrada = parse_data_iso(aberto.entrada_fila)

        if duracao_minutos_manual is None:
            duracao = max((fim - inicio).total_seconds() / 60, 0.0)
        else:
            if duracao_minutos_manual < 0:
                raise ValidationError("Duracao manual nao pode ser negativa.")
            duracao = float(duracao_minutos_manual)
        espera = max((inicio - entrada).total_seconds() / 60, 0.0)

        historico = HistoricoAtendimento(
            id=aberto.id,
            cliente_id=cliente.id,
            cliente_nome=cliente.nome,
            atendente_id=atendente.id,
            atendente_nome=atendente.nome,
            data_inicio=aberto.inicio_atendimento,
            data_fim=fim.isoformat(),
            duracao_minutos=round(duracao, 2),
            espera_minutos=round(espera, 2),
        )
        historico.validar()

        del self.atendimentos_abertos[aberto.id]
        atendente.atendimento_atual_id = None
        self.historico.append(historico)
        self.pilha_desfazer.empilhar(
            {
                "tipo": "finalizacao",
                "historico": historico.to_dict(),
                "atendimento_aberto": aberto.to_dict(),
            }
        )
        self._salvar()
        logger.info("Atendimento finalizado: atendimento=%s", historico.id)
        return historico

    def desfazer_ultima_finalizacao(self) -> AtendimentoAberto:
        acao = self.pilha_desfazer.desempilhar()
        if acao is None:
            raise BusinessRuleError("Nao ha finalizacao para desfazer.")
        try:
            if acao.get("tipo") != "finalizacao":
                raise BusinessRuleError("Acao de desfazer invalida.")
            historico = HistoricoAtendimento.from_dict(acao["historico"])
            aberto = AtendimentoAberto.from_dict(acao["atendimento_aberto"])
            atendente = self._obter_atendente(aberto.atendente_id)
            if atendente.ocupado and atendente.atendimento_atual_id != aberto.id:
                raise BusinessRuleError(
                    "Atendente esta ocupado; nao e possivel desfazer agora."
                )

            indice = self._indice_historico_por_id(historico.id)
            if indice is None:
                raise BusinessRuleError("Historico a desfazer nao foi encontrado.")
            self.historico.pop(indice)
            self.atendimentos_abertos[aberto.id] = aberto
            atendente.atendimento_atual_id = aberto.id
            self._salvar()
            logger.info("Finalizacao desfeita: atendimento=%s", aberto.id)
            return aberto
        except Exception:
            self.pilha_desfazer.empilhar(acao)
            raise

    def marcar_cliente_inativo(self, cliente_id: int) -> Cliente:
        cliente = self._obter_cliente(cliente_id)
        cliente.ativo = False
        self._salvar()
        logger.info("Cliente marcado como inativo: id=%s", cliente.id)
        return cliente

    def remover_clientes_inativos(self) -> list[int]:
        bloqueados = self._ids_clientes_em_fila_ou_abertos()
        removidos = self.lista_clientes.remover_inativos(self.clientes, bloqueados)
        for cliente_id in removidos:
            del self.clientes[cliente_id]
        self.indice_clientes.atualizar(self.clientes.values())
        self._salvar()
        logger.info("Clientes inativos removidos: ids=%s", removidos)
        return removidos

    def buscar_cliente_rapido(self, cliente_id: int, recursivo: bool = False) -> Cliente | None:
        if recursivo:
            return self.indice_clientes.buscar_por_id_recursivo(cliente_id)
        return self.indice_clientes.buscar_por_id(cliente_id)

    def historico_por_cliente(
        self,
        cliente_id: int,
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> list[HistoricoAtendimento]:
        self._obter_cliente(cliente_id)
        historicos = [item for item in self.historico if item.cliente_id == cliente_id]
        return self._filtrar_historico_por_data(historicos, data_inicio, data_fim)

    def filtrar_historico_por_data(
        self,
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> list[HistoricoAtendimento]:
        return self._filtrar_historico_por_data(self.historico, data_inicio, data_fim)

    def relatorio_tempo_medio(
        self,
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> dict[str, Any]:
        historicos = self.filtrar_historico_por_data(data_inicio, data_fim)
        total = self._somar_duracoes_recursivo(historicos, 0)
        quantidade = len(historicos)
        media = round(total / quantidade, 2) if quantidade else 0.0
        return {
            "quantidade_atendimentos": quantidade,
            "tempo_total_minutos": round(total, 2),
            "tempo_medio_minutos": media,
        }

    def top_5_clientes_mais_atendidos(self) -> list[dict[str, Any]]:
        contagem: dict[int, int] = {}
        for item in self.historico:
            contagem[item.cliente_id] = contagem.get(item.cliente_id, 0) + 1
        linhas = [
            {
                "cliente_id": cliente_id,
                "cliente_nome": self.clientes.get(cliente_id, Cliente(cliente_id, "Removido", "-")).nome,
                "total_atendimentos": total,
            }
            for cliente_id, total in contagem.items()
        ]
        ordenado = merge_sort(
            linhas,
            key=lambda linha: (linha["total_atendimentos"], -linha["cliente_id"]),
            reverse=True,
        )
        return ordenado[:5]

    def alertas_tempo_espera_alto(self, limite_minutos: float = 30.0) -> list[dict[str, Any]]:
        if limite_minutos < 0:
            raise ValidationError("Limite de espera nao pode ser negativo.")
        agora = datetime.now().replace(microsecond=0)
        alertas: list[dict[str, Any]] = []
        for nome_fila, fila in (
            ("prioridade", self.fila_prioridade),
            ("comum", self.fila_comum),
        ):
            for item in fila:
                espera = (agora - parse_data_iso(item.entrada_fila)).total_seconds() / 60
                if espera >= limite_minutos:
                    cliente = self.clientes.get(item.cliente_id)
                    alertas.append(
                        {
                            "atendimento_id": item.id,
                            "cliente_id": item.cliente_id,
                            "cliente_nome": cliente.nome if cliente else "Desconhecido",
                            "fila": nome_fila,
                            "espera_minutos": round(espera, 2),
                        }
                    )
        return merge_sort(alertas, key=lambda alerta: alerta["espera_minutos"], reverse=True)

    def exportar_relatorios_csv(
        self,
        pasta_destino: str | Path = "reports",
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> list[Path]:
        pasta = Path(pasta_destino)
        pasta.mkdir(parents=True, exist_ok=True)
        historicos = self.filtrar_historico_por_data(data_inicio, data_fim)
        arquivos: list[Path] = []

        caminho_historico = pasta / "historico_atendimentos.csv"
        self._escrever_csv(
            caminho_historico,
            [item.to_dict() for item in historicos],
            [
                "id",
                "cliente_id",
                "cliente_nome",
                "atendente_id",
                "atendente_nome",
                "data_inicio",
                "data_fim",
                "duracao_minutos",
                "espera_minutos",
            ],
        )
        arquivos.append(caminho_historico)

        caminho_media = pasta / "tempo_medio.csv"
        self._escrever_csv(
            caminho_media,
            [self.relatorio_tempo_medio(data_inicio, data_fim)],
            ["quantidade_atendimentos", "tempo_total_minutos", "tempo_medio_minutos"],
        )
        arquivos.append(caminho_media)

        caminho_top = pasta / "top_5_clientes.csv"
        self._escrever_csv(
            caminho_top,
            self.top_5_clientes_mais_atendidos(),
            ["cliente_id", "cliente_nome", "total_atendimentos"],
        )
        arquivos.append(caminho_top)

        caminho_alertas = pasta / "alertas_espera.csv"
        self._escrever_csv(
            caminho_alertas,
            self.alertas_tempo_espera_alto(),
            ["atendimento_id", "cliente_id", "cliente_nome", "fila", "espera_minutos"],
        )
        arquivos.append(caminho_alertas)

        logger.info("Relatorios CSV exportados: %s", [str(arquivo) for arquivo in arquivos])
        return arquivos

    def _escrever_csv(
        self,
        caminho: Path,
        linhas: list[dict[str, Any]],
        campos: list[str],
    ) -> None:
        with caminho.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=campos)
            escritor.writeheader()
            for linha in linhas:
                escritor.writerow({campo: linha.get(campo, "") for campo in campos})

    def _filtrar_historico_por_data(
        self,
        historicos: list[HistoricoAtendimento],
        data_inicio: str | None,
        data_fim: str | None,
    ) -> list[HistoricoAtendimento]:
        inicio = self._parse_data_filtro(data_inicio, fim_do_dia=False)
        fim = self._parse_data_filtro(data_fim, fim_do_dia=True)
        resultado: list[HistoricoAtendimento] = []
        for item in historicos:
            data_item = parse_data_iso(item.data_fim)
            if inicio and data_item < inicio:
                continue
            if fim and data_item > fim:
                continue
            resultado.append(item)
        return resultado

    def _parse_data_filtro(self, valor: str | None, fim_do_dia: bool) -> datetime | None:
        if not valor:
            return None
        try:
            if "T" in valor:
                return datetime.fromisoformat(valor)
            data = date.fromisoformat(valor)
            if fim_do_dia:
                return datetime.combine(data, datetime.max.time()).replace(microsecond=0)
            return datetime.combine(data, datetime.min.time())
        except ValueError as exc:
            raise ValidationError("Filtro de data deve estar em YYYY-MM-DD ou ISO completo.") from exc

    def _somar_duracoes_recursivo(
        self,
        historicos: list[HistoricoAtendimento],
        indice: int,
    ) -> float:
        if indice >= len(historicos):
            return 0.0
        return historicos[indice].duracao_minutos + self._somar_duracoes_recursivo(
            historicos,
            indice + 1,
        )

    def _indice_historico_por_id(self, historico_id: int) -> int | None:
        for indice in range(len(self.historico) - 1, -1, -1):
            if self.historico[indice].id == historico_id:
                return indice
        return None

    def _cliente_tem_atendimento_em_andamento(self, cliente_id: int) -> bool:
        return cliente_id in self._ids_clientes_em_fila_ou_abertos()

    def _ids_clientes_em_fila_ou_abertos(self) -> set[int]:
        ids = self.fila_prioridade.ids_clientes() | self.fila_comum.ids_clientes()
        ids.update(aberto.cliente_id for aberto in self.atendimentos_abertos.values())
        return ids
