# Projeto 2 - Sistema Completo de Atendimento e Analise

Sistema em Python para gerenciamento de atendimentos de uma clinica ou central de atendimento. O projeto cobre cadastro de clientes e atendentes, filas comum e prioritaria, historico, relatorios, CSV, persistencia, logs, testes e justificativa de Big-O.

## Funcionalidades atendidas

- Cadastro de clientes com id, nome, telefone, prioridade e status ativo.
- Cadastro de atendentes.
- Abertura de atendimento com entrada na fila correta.
- Fila de prioridade e fila comum com ordem de chegada preservada.
- Chamada do proximo cliente, sempre dando preferencia a prioridade.
- Finalizacao de atendimento com data, duracao, atendente e espera.
- Historico de atendimentos por cliente.
- Desfazer a ultima finalizacao com pilha.
- Remocao de clientes inativos usando lista encadeada.
- Relatorio de tempo medio de atendimento.
- Exportacao de relatorios em CSV.
- Busca rapida por cliente usando vetor ordenado por id e busca binaria.
- Filtro por data, top 5 clientes mais atendidos e alertas de espera alta.
- Persistencia em arquivo JSON.
- Logs de operacoes importantes.
- Testes unitarios basicos.

## Estrutura do projeto

```text
Projeto-2---E.-Dados/
├── data/                    # Dados de exemplo e dados reais do sistema
├── docs/                    # Relatorio curto com Big-O e escolhas
├── logs/                    # Logs gerados em tempo de execucao
├── reports/                 # CSVs exportados
├── src/atendimento/         # Codigo-fonte modularizado
├── tests/                   # Testes unitarios
├── main.py                  # Entrada principal
├── requirements.txt         # Dependencias
└── README.md
```

## Como executar

Requisito: Python 3.10 ou superior.

```bash
python main.py
```

Para executar usando os dados de exemplo sem alterar o arquivo padrao:

```bash
python main.py --data data/sample_data.json
```

O menu do terminal permite escolher as operacoes pelo numero.

## Como executar os testes

```bash
python -m unittest discover -s tests
```

## Como exportar relatorios CSV

Pelo menu, escolha a opcao `11 - Exportar relatorios CSV`. Os arquivos serao gerados em `reports/` por padrao:

- `historico_atendimentos.csv`
- `tempo_medio.csv`
- `top_5_clientes.csv`
- `alertas_espera.csv`

## Dados de exemplo

O arquivo `data/sample_data.json` contem clientes, atendentes, filas e historico para demonstracao. O arquivo `data/atendimento_data.json` e o arquivo padrao usado pelo sistema.

## Regras de negocio implementadas

- Cliente prioritario sempre e chamado antes da fila comum.
- Dentro de cada fila, a ordem de chegada e preservada.
- Um atendente nao pode atender mais de um cliente ao mesmo tempo.
- Nao e permitido finalizar atendimento se o atendente nao possui atendimento aberto.
- Nao e permitido remover cliente inativo se ele estiver em fila ou com atendimento aberto.
- O mesmo cliente nao pode ter dois atendimentos simultaneos em fila ou aberto.

## Estruturas e algoritmos usados

- Vetor ordenado por id: busca binaria de clientes, O(log n).
- Vetor nao ordenado: cadastros temporarios, insercao O(1).
- Fila prioritaria: clientes urgentes em FIFO.
- Fila comum: clientes normais em FIFO.
- Pilha: desfaz a ultima finalizacao, LIFO.
- Lista encadeada: remocao de clientes inativos.
- Merge sort: ordenacao dos relatorios, O(n log n).
- Recursao: busca binaria recursiva, soma recursiva de duracoes e merge sort.

Mais detalhes estao em `docs/relatorio_estruturas.md`.

## Repositorio do projeto

Link para envio ao professor:

```text
https://github.com/SwintexD/Projeto-2---E.-Dados
```

Se o repositorio estiver privado, adicione o professor como colaborador no GitHub.
