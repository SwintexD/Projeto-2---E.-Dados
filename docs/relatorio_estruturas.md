# Relatorio curto - estruturas, Big-O e escolhas

## Objetivo

O sistema foi construido para simular o atendimento de uma clinica ou central de atendimento, com cadastro, filas, historico, relatorios e analise de desempenho. A arquitetura separa dados, regras de negocio e interface de terminal.

## Organizacao em camadas

- `models.py`: entidades do dominio, como Cliente, Atendente, AtendimentoFila, AtendimentoAberto e HistoricoAtendimento.
- `structures.py`: estruturas obrigatorias do projeto.
- `service.py`: regras de negocio e relatorios.
- `data_store.py`: persistencia em JSON.
- `cli.py`: interface de terminal.
- `tests/`: testes unitarios.

## Estruturas obrigatorias

### Vetor ordenado para busca binaria

A classe `VetorOrdenadoClientes` mantem os clientes ordenados por id. A busca por id usa busca binaria iterativa ou recursiva.

- Busca: O(log n)
- Recriacao do indice apos cadastro/remocao: O(n log n)
- Justificativa: melhora a busca rapida por id quando existem muitos clientes.

### Vetor nao ordenado para cadastros temporarios

A lista `clientes_temporarios` guarda clientes antes da efetivacao no cadastro final.

- Insercao no fim: O(1)
- Busca por duplicidade: O(n)
- Justificativa: cadastros temporarios nao exigem ordenacao imediata.

### Fila de prioridade

A fila de prioridade guarda clientes com `prioridade=True`. Ela e FIFO, portanto preserva a ordem de chegada entre clientes prioritarios.

- Enfileirar: O(1)
- Desenfileirar: O(1)
- Justificativa: prioridade sempre deve ser chamada antes da fila comum, mas sem perder a ordem de chegada.

### Fila comum

A fila comum guarda clientes sem prioridade.

- Enfileirar: O(1)
- Desenfileirar: O(1)
- Justificativa: e a estrutura correta para atendimento por ordem de chegada.

### Pilha para desfazer

A classe `PilhaDesfazer` armazena a ultima finalizacao. Ao desfazer, o historico e removido e o atendimento volta a ficar aberto.

- Empilhar: O(1)
- Desempilhar: O(1)
- Justificativa: desfazer segue LIFO, isto e, a ultima acao e a primeira a ser revertida.

### Lista encadeada

A classe `ListaEncadeadaClientes` percorre os clientes para remover inativos, respeitando a regra de nao remover cliente em fila ou em atendimento aberto.

- Insercao no fim: O(n)
- Remocao de inativos: O(n)
- Justificativa: atende o requisito de uso de lista encadeada e permite remocao durante percurso.

### Ordenacao para relatorios

O projeto usa merge sort em `sorting.py`, principalmente no top 5 de clientes e nos alertas de espera.

- Complexidade: O(n log n)
- Justificativa: merge sort tem desempenho estavel e demonstra ordenacao recursiva.

### Recursao

A recursao aparece em tres rotinas:

- Busca binaria recursiva no vetor ordenado.
- Soma recursiva das duracoes no relatorio de tempo medio.
- Merge sort recursivo nos relatorios.

## Big-O das operacoes principais

| Operacao | Estrutura principal | Big-O |
|---|---|---|
| Cadastrar cliente | dicionario + vetor ordenado | O(n log n) por recriar indice |
| Buscar cliente por id | vetor ordenado | O(log n) |
| Abrir atendimento | fila | O(1) |
| Chamar proximo | filas prioridade/comum | O(1) |
| Finalizar atendimento | historico + pilha | O(1) amortizado |
| Historico por cliente | lista de historico | O(h) |
| Desfazer ultima finalizacao | pilha + historico | O(h) no pior caso |
| Remover inativos | lista encadeada | O(n) |
| Tempo medio | historico | O(h) |
| Top 5 clientes | contagem + merge sort | O(h + c log c) |
| Alertas de espera | filas + merge sort | O(f log f) |
| Exportar CSV | historico/relatorios | O(h + c log c + f log f) |

Legenda: `n` = clientes, `h` = historicos, `c` = clientes com historico, `f` = atendimentos em fila.

## Tratamento de erros

Foram criadas excecoes especificas:

- `ValidationError`: entradas invalidas.
- `NotFoundError`: cliente ou atendente inexistente.
- `BusinessRuleError`: violacao de regras de negocio.

A interface de terminal captura esses erros e exibe mensagens amigaveis, evitando travamentos em entradas invalidas.

## Persistencia

A persistencia e feita em JSON pelo `DataStore`. Toda alteracao relevante chama `_salvar()`. O arquivo padrao e `data/atendimento_data.json`.

## Logs

Operacoes importantes sao registradas em `logs/operacoes.log`, como cadastro, abertura, chamada, finalizacao, desfazer e exportacao de CSV.

## Conclusao

O projeto atende aos requisitos obrigatorios e extras, com separacao por camadas, uso das estruturas exigidas, justificativa de complexidade, persistencia, tratamento de erros e testes unitarios basicos.
