# Analisando Grafos do SNAP — `email-EuAll`

Trabalho prático da disciplina de Teoria dos Grafos (IC/UFBA): tratamento, análise
estrutural, implementação de algoritmos clássicos e estudo de propriedades
(small-world, lei de potência e robustez) sobre um grafo real do
[SNAP](https://snap.stanford.edu/data/index.html).

## Grafo atribuído

Regra: `G = (S × (U + 1)) mod 129` (se 0, usa-se 129), onde `S` é a soma dos dígitos
da matrícula e `U` são os seus dois últimos dígitos.

| Matrícula | S | U | Cálculo | Grafo |
|---|---|---|---|---|
| 224216275 | 31 | 75 | (31 × 76) mod 129 = 2356 mod 129 = 34 | **G34 – `email-EuAll`** |

[`email-EuAll`](https://snap.stanford.edu/data/email-EuAll.html): rede de e-mails de uma
instituição de pesquisa europeia — grafo dirigido com 265.214 vértices e 420.045 arestas.

## Estrutura

```
scripts/          download dos dados brutos
data/raw/         dados brutos do SNAP (não versionados)
data/processed/   grafo tratado
src/              tratamento, métricas e análises
src/algorithms/   implementações próprias dos algoritmos
notebooks/        notebook de análise
tests/            testes comparando as implementações com o NetworkX
results/          tabelas (CSV) e figuras geradas
```

## Requisitos

Python 3.10+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

## Execução

### 1. Download dos dados brutos

```bash
python scripts/download_data.py
```

Baixa `email-EuAll.txt.gz` do SNAP para `data/raw/` (não versionado) e confere se o
arquivo tem os 265.214 vértices e 420.045 arestas declarados pelo SNAP.
Use `--force` para baixar novamente.

### 2. Tratamento

```bash
python -m src.treatment
```

Aplica, nesta ordem: remoção de auto-loops → conversão para não dirigido simples →
extração da maior componente conexa. Gera `results/tables/tratamento_evolucao.csv`:

| Etapa | Vértices | Arestas |
|---|---:|---:|
| Grafo bruto (dirigido) | 265.214 | 420.045 |
| Após remoção de auto-loops (dirigido) | 265.214 | 418.956 |
| Após conversão para não dirigido simples | 265.214 | 364.481 |
| Maior componente conexa (LCC) | 224.832 | 339.925 |

### 3. Conjunto de dados tratado

```bash
python -m src.prepare_data
```

Gera (e versiona) em `data/processed/`:

| Arquivo | Conteúdo |
|---|---|
| `lcc.edgelist.gz` | LCC não dirigida (224.832 vértices, 339.925 arestas), ids renumerados `0..n-1`, colunas `u v w` |
| `lcc_node_map.csv.gz` | correspondência `novo_id → id_original` do SNAP |
| `directed_no_loops.edgelist.gz` | grafo dirigido sem auto-loops (265.214 vértices, 418.956 arestas), usado no Tarjan |
| `subgraph_300.edgelist.gz` | subgrafo induzido de 300 vértices (372 arestas), obtido por BFS na LCC, usado no Bellman-Ford e no Floyd-Warshall |

O grafo original é **não ponderado**. Para os algoritmos ponderados foram atribuídos
pesos sintéticos inteiros uniformes em `[1, 10]` (semente 42). O subgrafo herda os pesos da LCC.

### 4. Parte I – Métricas estruturais

```bash
python -m src.metrics
```

Gera em `results/tables/`: `parte1_basicas.csv` (vértices, arestas, graus, densidade,
componentes; grafo completo e LCC), `componentes_tamanhos.csv` (tamanho de **cada**
componente), `componentes_frequencia.csv`; e em `results/figures/`: `componentes_tamanhos.png`.

```bash
python -m src.distances
```

Na LCC: diâmetro e raio **exatos** pelo algoritmo *BoundingDiameters* (Takes & Kosters,
2011) e comprimento médio dos caminhos **estimado** por BFS a partir de 100 e 500 fontes
aleatórias (IC 95%). Gera `parte1_diametro_raio.csv` e `parte1_caminhos_amostragem.csv`.

```bash
python -m src.clustering
```

Número de triângulos (algoritmo *forward*), coeficiente de clusterização médio e
transitividade, no grafo completo e na LCC. Gera `parte1_clusterizacao.csv`.

```bash
python -m src.visualize
python -m src.part1_summary
```

Distribuição de graus (`distribuicao_graus.csv/.png`, escalas linear e log-log),
visualização de uma amostra de 300 vértices em torno dos 5 maiores hubs
(`visualizacao_amostra.png`) e a tabela-resumo da Parte I com o status de cada medida,
computada, aproximada ou não computada, e o método (`parte1_resumo.csv`).

| Medida | Grafo completo | LCC | Status |
|---|---:|---:|---|
| Vértices | 265.214 | 224.832 | exato |
| Arestas | 364.481 | 339.925 | exato |
| Grau mín / máx / médio | 0 / 7.636 / 2,75 | 1 / 7.636 / 3,02 | exato |
| Densidade | 1,04×10⁻⁵ | 1,34×10⁻⁵ | exato |
| Componentes conexas | 15.836 | 1 | exato |
| Diâmetro / raio | ∞ (desconexo) | 14 / 7 | exato |
| Comprimento médio dos caminhos | – | 4,13 (IC 95%: 4,10–4,16) | amostragem |
| Clusterização média | 0,0671 | 0,0791 | exato |
| Triângulos | 267.313 | 267.313 | exato |

### 5. Parte II – Algoritmos

Implementações próprias em `src/algorithms/`, todas conferidas com o NetworkX em `tests/`:

| Algoritmo | Arquivo | Grafo | Complexidade |
|---|---|---|---|
| BFS | `bfs.py` | LCC | O(V+E) |
| DFS (iterativa) | `dfs.py` | LCC | O(V+E) |
| Eulerianidade (+ Hierholzer) | `euler.py` | LCC e grafo dirigido | O(V+E) |
| Dijkstra (heap) | `dijkstra.py` | LCC com pesos sintéticos | O((V+E) log V) |
| Bellman-Ford | `bellman_ford.py` | subgrafo de 300 vértices | O(V·E) |
| Floyd-Warshall (puro e numpy) | `floyd_warshall.py` | subgrafo de 300 vértices | O(V³) |
| Tarjan: SCC e pontes/articulações | `tarjan.py` | grafo dirigido / LCC | O(V+E) |
| Prim (heap) e Kruskal (union-find) | `mst.py` | LCC com pesos sintéticos | O(E log V) |

```bash
python -m src.benchmark          # completo: 30 execuções (10 no Floyd-Warshall puro), ~5 min
python -m src.benchmark --quick  # verificação rápida
```

Gera `parte2_tempos.csv` (média, desvio e IC 95%: Normal/Z para n ≥ 30, t-Student
para n < 30), `parte2_resultados.csv` (saída de cada algoritmo), `parte2_escala.csv` e
`parte2_expoentes.csv` (tempo × tamanho da entrada; a inclinação em log-log é o
expoente observado), além das figuras `tempos_algoritmos.png` e `escala_algoritmos.png`.

### Testes

```bash
python -m pytest
```

> Os demais passos serão adicionados ao longo do desenvolvimento.
