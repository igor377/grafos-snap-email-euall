# Analisando Grafos do SNAP: `email-EuAll`

Trabalho prático de **Teoria dos Grafos** (Instituto de Computação, UFBA). Aplica os conceitos
da disciplina a um grafo real do [SNAP](https://snap.stanford.edu/data/index.html):

- tratamento dos dados;
- análise estrutural (Parte I);
- implementação e medição de tempo dos algoritmos clássicos (Parte II);
- investigação de small-world, lei de potência e robustez (Parte III).

Todos os algoritmos e análises são **implementações próprias**. O NetworkX é usado apenas
para conferir os resultados nos testes e para desenhar a visualização.

## Grafo atribuído

Regra: `G = (S × (U + 1)) mod 129` (se o resultado for 0, usa-se 129), onde `S` é a soma
dos dígitos da matrícula e `U` são os seus dois últimos dígitos.

| Matrícula | S | U | Cálculo | Grafo |
|---|---|---|---|---|
| 224216275 | 2+2+4+2+1+6+2+7+5 = 31 | 75 | (31 × 76) mod 129 = 2356 mod 129 = **34** | **G34: `email-EuAll`** |

[`email-EuAll`](https://snap.stanford.edu/data/email-EuAll.html) é a rede de e-mails de uma
instituição de pesquisa europeia, de out/2003 a mar/2005. É um grafo **dirigido** com
265.214 vértices e 420.045 arestas, em que u → v significa que u enviou ao menos um e-mail a v.

## Execução rápida

```bash
python -m venv .venv
.venv\Scripts\activate              # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python scripts/run_all.py           # pipeline completo (~40 min)
python -m pytest                    # testes (~10 s)
jupyter notebook notebooks/analise.ipynb
```

Requer **Python 3.10+**. O projeto foi testado com Python 3.14.3, numpy 2.5.5, scipy 1.18.1,
pandas 3.1.1, matplotlib 3.11.2, networkx 3.7, pytest 9.2.0 e jupyter 1.1.1.

Os resultados (`results/`) e o grafo tratado (`data/processed/`) já estão versionados.
Para apenas consultar, basta abrir o notebook ou os arquivos em `results/`, sem executar nada.

## Estrutura

```
scripts/
  download_data.py        baixa o grafo bruto do SNAP e confere |V| e |E|
  run_all.py              executa o pipeline inteiro, em ordem
data/
  raw/                    grafo bruto (não versionado; baixado pelo script)
  processed/              grafo tratado (versionado)
src/
  load.py                 leitura/escrita de edgelists e caminhos do projeto
  treatment.py            tratamento: auto-loops, não dirigido, LCC
  prepare_data.py         gera data/processed/ (LCC, grafo dirigido, subgrafo, pesos)
  metrics.py              Parte I: graus, densidade, componentes
  distances.py            Parte I: diâmetro, raio, caminho médio
  clustering.py           Parte I: triângulos e clusterização
  visualize.py            Parte I: distribuição de graus e visualização
  part1_summary.py        Parte I: tabela "computado / aproximado / não computado"
  benchmark.py            Parte II: tempos, IC 95% e experimento de escala
  smallworld.py           Parte III: small-world (gerador Erdős–Rényi próprio)
  powerlaw.py             Parte III: lei de potência
  robustness.py           Parte III: robustez a remoção aleatória e direcionada
  report_tables.py        gera as tabelas LaTeX do relatório a partir dos CSVs
  algorithms/             BFS, DFS, Euler, Dijkstra, Bellman-Ford, Floyd-Warshall,
                          Tarjan, Prim, Kruskal, PageRank
notebooks/analise.ipynb   reúne todas as tabelas e figuras
tests/                    testes (implementações conferidas com o NetworkX)
results/tables/           resultados em CSV
results/figures/          figuras em PNG e em PDF vetorial (para o LaTeX)
results/latex/            tabelas LaTeX geradas (tab_*.tex), prontas para \input
```

## Pipeline passo a passo

Todos os comandos são executados a partir da raiz do projeto. `scripts/run_all.py` executa
todos eles nesta ordem.

| # | Comando | O que faz | Saídas principais | Tempo* |
|---|---|---|---|---|
| 1 | `python scripts/download_data.py` | Baixa `email-EuAll.txt.gz` e confere 265.214 / 420.045 | `data/raw/` | 2 s |
| 2 | `python -m src.treatment` | Tratamento e tabela de evolução | `tratamento_evolucao.csv` | 5 s |
| 3 | `python -m src.prepare_data` | Grafo tratado, subgrafo de 300 vértices, pesos sintéticos | `data/processed/*` | 10 s |
| 4 | `python -m src.metrics` | Graus, densidade, componentes e o tamanho de cada uma | `parte1_basicas.csv`, `componentes_*.csv` | 10 s |
| 5 | `python -m src.distances` | Diâmetro e raio exatos; caminho médio por amostragem | `parte1_diametro_raio.csv`, `parte1_caminhos_amostragem.csv` | 1,5 min |
| 6 | `python -m src.clustering` | Triângulos, clusterização, transitividade | `parte1_clusterizacao.csv` | 10 s |
| 7 | `python -m src.visualize` | Distribuição de graus e visualização de amostra | `distribuicao_graus.*`, `visualizacao_amostra.png` | 15 s |
| 8 | `python -m src.part1_summary` | Tabela-resumo da Parte I | `parte1_resumo.csv` | 1 s |
| 9 | `python -m src.benchmark` | Tempo de todos os algoritmos (30 execuções) e escala dos 9 algoritmos (30 repetições por tamanho, IC 95%) | `parte2_*.csv`, `tempos_algoritmos.*`, `escala_algoritmos.*` | 17 min |
| 10 | `python -m src.smallworld` | Small-world contra 5 grafos Erdős–Rényi | `parte3_smallworld*.csv` | 10 min |
| 11 | `python -m src.powerlaw` | Lei de potência | `parte3_powerlaw*.csv`, `lei_de_potencia.png` | 5 s |
| 12 | `python -m src.robustness` | Robustez: 30 remoções aleatórias + ataques por grau e por PageRank | `parte3_robustez*.csv`, `robustez.*` | 7 min |
| 13 | `python -m src.report_tables` | Tabelas LaTeX do relatório a partir dos CSVs | `results/latex/tab_*.tex` | 1 s |

\* Tempos aproximados num notebook comum. `benchmark` e `robustness` aceitam `--quick`
para uma execução reduzida e `--plots-only` para só redesenhar as figuras a partir dos
CSVs; `benchmark --scaling-only` refaz apenas o experimento de escala.

## Tratamento dos dados

| Etapa | Vértices | Arestas |
|---|---:|---:|
| Grafo bruto (dirigido) | 265.214 | 420.045 |
| Remoção de 1.089 auto-loops | 265.214 | 418.956 |
| Dirigido → não dirigido simples (u→v e v→u viram uma aresta) | 265.214 | 364.481 |
| Maior componente conexa (LCC) | 224.832 | 339.925 |

- Não há etapa temporal nem de multigrafo: o SNAP distribui o grafo já agregado no período
  e sem arestas repetidas.
- A política adotada para o grafo desconexo é trabalhar na LCC, que tem 84,8% dos vértices
  e 93,3% das arestas.
- O grafo dirigido sem auto-loops também é mantido, para o algoritmo de Tarjan (componentes
  fortemente conexas).

Arquivos em `data/processed/` (o `.gz` é gerado de forma determinística):

| Arquivo | Conteúdo |
|---|---|
| `lcc.edgelist.gz` | LCC não dirigida, ids renumerados `0..n-1`, colunas `u v w` |
| `lcc_node_map.csv.gz` | correspondência `novo_id → id_original` do SNAP |
| `directed_no_loops.edgelist.gz` | grafo dirigido sem auto-loops (ids originais) |
| `subgraph_300.edgelist.gz` | subgrafo induzido de 300 vértices (372 arestas), obtido por BFS na LCC |

O grafo é **não ponderado**. Para Dijkstra, Bellman-Ford, Floyd-Warshall, Prim e Kruskal
foram atribuídos **pesos sintéticos inteiros uniformes em [1, 10]** (semente 42). O subgrafo
herda os pesos da LCC.

## Resultados principais

### Parte I: análise estrutural

| Medida | Grafo completo | LCC | Como |
|---|---:|---:|---|
| Vértices / arestas | 265.214 / 364.481 | 224.832 / 339.925 | exato |
| Grau mín / máx / médio | 0 / 7.636 / 2,75 | 1 / 7.636 / 3,02 | exato |
| Densidade | 1,04×10⁻⁵ | 1,34×10⁻⁵ | exato |
| Componentes conexas | 15.836 | 1 | exato (BFS) |
| Diâmetro / raio | ∞ (desconexo) | **14 / 7** | exato (*BoundingDiameters*, 4 BFS) |
| Comprimento médio dos caminhos | – | 4,13 (IC 95%: 4,10–4,16) | BFS a partir de 500 fontes |
| Clusterização média | 0,0671 | 0,0791 | exato |
| Triângulos | 267.313 | 267.313 | exato (algoritmo *forward*) |

A tabela completa com o status de cada medida está em `results/tables/parte1_resumo.csv`.

### Parte II: algoritmos

Tempos com 30 execuções e IC 95% pela Normal (Z). O Floyd-Warshall em Python puro teve
10 execuções, com IC pela t-Student.

| Algoritmo | Grafo | Complexidade | Média (s) | IC 95% (s) |
|---|---|---|---:|---|
| BFS | LCC | O(V+E) | 0,198 | [0,183; 0,213] |
| DFS (iterativa) | LCC | O(V+E) | 0,320 | [0,316; 0,323] |
| Eulerianidade | LCC | O(V+E) | 0,166 | [0,165; 0,167] |
| Dijkstra (heap) | LCC ponderada | O((V+E) log V) | 0,770 | [0,767; 0,774] |
| Bellman-Ford | subgrafo 300 | O(V·E) | 0,0003 | [0,0003; 0,0003] |
| Floyd-Warshall (Python puro) | subgrafo 300 | O(V³) | 1,952 | [1,940; 1,964] |
| Floyd-Warshall (numpy) | subgrafo 300 | O(V³) | 0,057 | [0,057; 0,058] |
| Tarjan (SCC) | grafo dirigido | O(V+E) | 0,607 | [0,603; 0,611] |
| Tarjan (pontes/articulações) | LCC | O(V+E) | 0,577 | [0,569; 0,586] |
| Prim (heap) | LCC ponderada | O(E log V) | 0,904 | [0,897; 0,910] |
| Kruskal (union-find) | LCC ponderada | O(E log V) | 0,526 | [0,523; 0,529] |

Tempos variam de máquina para máquina. Os valores acima foram medidos no ambiente de
desenvolvimento, e a saída de cada algoritmo está em `results/tables/parte2_resultados.csv`.

**Complexidade observada dos 9 algoritmos.** Cada algoritmo foi medido em subgrafos de
tamanho crescente (prefixos da ordem de BFS da LCC, todos conexos), com 30 repetições e
IC 95% por tamanho. O tempo médio é ajustado em log-log contra a função teórica f(n):
**inclinação 1** significa que f(n) descreve bem o custo observado
(`parte2_expoentes.csv`, `escala_algoritmos.png`).

| Algoritmo | f(n) | Inclinação (R²) | Vértices testados |
|---|---|---:|---|
| BFS | V+E | 1,49 (0,999) | 14 mil – 224.832 |
| DFS | V+E | 1,27 (0,990) | 14 mil – 224.832 |
| Eulerianidade | V+E | 1,31 (0,998) | 14 mil – 224.832 |
| Tarjan (pontes/articulações) | V+E | 0,98 (0,987) | 14 mil – 224.832 |
| Dijkstra | (V+E) log V | 1,31 (0,999) | 14 mil – 224.832 |
| Prim | E log V | 1,06 (0,995) | 14 mil – 224.832 |
| Kruskal | E log V | 1,05 (0,998) | 14 mil – 224.832 |
| Bellman-Ford | V·E | 0,61 (0,979) | 1 mil – 16 mil |
| Floyd-Warshall | V³ | 1,00 (1,000) | 50 – 300 |

Como ler:
- **Floyd-Warshall, Tarjan, Prim e Kruskal** confirmam a complexidade teórica (≈ 1).
- **Bellman-Ford fica bem abaixo de 1** porque o V·E é o pior caso. Com a parada
  antecipada, ele convergiu em só 4 ou 5 rodadas em todos os tamanhos, então o custo real
  foi proporcional a k·E, com k pequeno.
- **BFS, DFS, Eulerianidade e Dijkstra ficam acima de 1** (1,27 a 1,49), com R² ≥ 0,99, ou
  seja, não é ruído. O número de operações é linear: os testes confirmam que cada vértice
  entra uma vez na fila ou na pilha. O que cresce é o custo de cada operação em Python.
  Como o Tarjan percorre as mesmas listas e ficou em 0,98, o tamanho do grafo sozinho não
  explica o desvio. A hipótese, não isolada experimentalmente, é de efeitos do
  interpretador, como a alocação de listas de tamanho V e o gerenciamento de memória. A
  faixa testada, de pouco mais de uma ordem de grandeza, também limita a precisão do
  expoente.

### Parte III: propriedades da rede

| Pergunta | Resultado |
|---|---|
| Small-world? | **Sim**: C = 0,079 contra C_rand ≈ 0,000008 (cerca de 10⁴ vezes maior); L = 4,13 contra L_rand ≈ 11,1; σ ≈ 2,7×10⁴ |
| Lei de potência? | **Aproximadamente**: cauda pesada, com γ ≈ 1,9–2,0 nos ajustes lineares, mas dois regimes (γ ≈ 2,8 na cabeça e γ ≈ 1,7 na cauda, por máxima verossimilhança) e corte acima de k ≈ 1.000 |
| Robusto à remoção aleatória de 5%? | **Sim**: a maior componente mantém 90,7% ± 1,7% dos vértices |
| Robusto à remoção dos 5% mais centrais? | **Não**: atacando pelo **grau**, a maior componente cai para 6 vértices (99,7% isolados); pelo **PageRank** (implementação própria), para 3 vértices (99,8% isolados). As duas centralidades escolhem 93% dos mesmos alvos |

## Relatório

O relatório (template WebMedia) não é versionado: é entregue como PDF. Suas tabelas são
geradas por `python -m src.report_tables` em `results/latex/` (e copiadas para
`relatorio/tabelas/`, se essa pasta existir), e as figuras são os PDFs vetoriais de
`results/figures/`. Assim, nenhum número das tabelas do relatório é digitado à mão.

## Reprodutibilidade

- **Sementes fixas** (42) em todo sorteio: pesos sintéticos, subgrafo, amostras de BFS,
  grafos Erdős–Rényi e remoções aleatórias. Reexecutar o pipeline reproduz as mesmas
  tabelas e figuras; só os tempos da Parte II variam.
- Os `.gz` de `data/processed/` são gravados sem data de criação, então reexecutar não
  altera os arquivos versionados.
- Cada algoritmo próprio é conferido com o NetworkX em `tests/`
  (`python -m pytest`, 110 testes).

## Referências

- J. Leskovec, J. Kleinberg, C. Faloutsos. *Graph Evolution: Densification and Shrinking
  Diameters*. ACM TKDD, 2007. (dataset `email-EuAll`)
- F. W. Takes, W. A. Kosters. *Determining the Diameter of Small World Networks*. CIKM, 2011.
- T. Schank, D. Wagner. *Finding, Counting and Listing All Triangles in Large Graphs*. WEA, 2005.
- A. Clauset, C. R. Shalizi, M. E. J. Newman. *Power-Law Distributions in Empirical Data*.
  SIAM Review, 2009.
- D. J. Watts, S. H. Strogatz. *Collective dynamics of "small-world" networks*. Nature, 1998.
- R. Albert, H. Jeong, A.-L. Barabási. *Error and attack tolerance of complex networks*.
  Nature, 2000.
- T. H. Cormen et al. *Introduction to Algorithms*. 4. ed. MIT Press, 2022.
