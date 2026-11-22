# Analisando Grafos do SNAP: `email-EuAll`

Trabalho prático de **Teoria dos Grafos** (Instituto de Computação, UFBA). Aplica os conceitos
da disciplina a um grafo real do [SNAP](https://snap.stanford.edu/data/index.html):
tratamento dos dados, análise estrutural (Parte I), algoritmos clássicos com medição de tempo
(Parte II) e small-world, lei de potência e robustez (Parte III).

Todos os algoritmos e análises são **implementações próprias**. O NetworkX é usado apenas
para conferir os resultados nos testes e para desenhar a visualização.

📄 **Relatório: [`relatorio/224216275.pdf`](relatorio/224216275.pdf)** (template WebMedia).
Os resultados detalhados e a discussão estão nele.

## Grafo atribuído

Regra: `G = (S × (U + 1)) mod 129`, onde `S` é a soma dos dígitos da matrícula e `U` são os
seus dois últimos dígitos.

| Matrícula | S | U | Cálculo | Grafo |
|---|---|---|---|---|
| 224216275 | 2+2+4+2+1+6+2+7+5 = 31 | 75 | (31 × 76) mod 129 = 2356 mod 129 = **34** | **G34: `email-EuAll`** |

[`email-EuAll`](https://snap.stanford.edu/data/email-EuAll.html) é a rede de e-mails de uma
instituição de pesquisa europeia (out/2003 a mar/2005): grafo **dirigido** com 265.214
vértices e 420.045 arestas, em que u → v significa que u enviou ao menos um e-mail a v.

## Instalação e execução

```bash
python -m venv .venv
.venv\Scripts\activate              # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt     # ou requirements-lock.txt (versões exatas)

python -m pytest                    # 124 testes (~1 min)
python scripts/run_all.py --quick   # pipeline reduzido
python scripts/run_all.py           # pipeline completo (~1 h 15 min)
jupyter notebook notebooks/analise.ipynb
```

- **Testado com Python 3.12.10 e 3.14.3** (testes e pipeline reduzido), com numpy 2.5.5,
  scipy 1.18.1, pandas 3.1.1, matplotlib 3.11.2 e networkx 3.7. Requer Python 3.10+.
- `results/` e `data/processed/` já estão versionados: para só consultar, abra o notebook
  (com `RECOMPUTE = False`) ou os arquivos em `results/`, sem executar nada.
- `run_all.py` baixa o grafo bruto (`scripts/download_data.py`) e executa cada módulo de
  `src/` em ordem. Cada um também roda sozinho: `python -m src.<modulo>`. `benchmark` e
  `robustness` aceitam `--quick` (reduzido) e `--plots-only` (só redesenha as figuras).
- Sementes fixas (42) em todo sorteio: reexecutar reproduz as mesmas tabelas e figuras;
  só os tempos da Parte II variam com a máquina.

## Requisitos do enunciado → onde estão

Resultados em `results/tables/` (CSV) e `results/figures/` (PNG/PDF).

| Requisito | Código | Resultado | Relatório |
|---|---|---|---|
| Cálculo do grafo pela matrícula | — | tabela acima | §2 |
| Tratamento dos dados (e informá-lo) | `src/treatment.py`, `src/prepare_data.py` | `tratamento_evolucao.csv`, `data/processed/` | §5 |
| **Parte I** – vértices, arestas, graus, densidade | `src/metrics.py` | `parte1_basicas.csv` | §7.1 |
| Parte I – nº de componentes e **tamanho de cada uma** | `src/metrics.py` | `componentes_tamanhos.csv`, `componentes_frequencia.csv`, `componentes_tamanhos.png` | §7.1 |
| Parte I – distribuição de graus | `src/visualize.py` | `distribuicao_graus.csv`, `distribuicao_graus.png` | §7.1 |
| Parte I – diâmetro e raio (exatos) | `src/distances.py` (*BoundingDiameters*) | `parte1_diametro_raio.csv` | §6, §7.1 |
| Parte I – comprimento médio dos caminhos (exato) | `src/distances.py` (redução das folhas) | `parte1_caminho_exato.csv` | §6, §7.1 |
| Parte I – clusterização média e triângulos | `src/clustering.py` | `parte1_clusterizacao.csv` | §7.1 |
| Parte I – visualização | `src/visualize.py` | `visualizacao_amostra.png` | §7.1 |
| Parte I – tabela "computado ou não" | `src/part1_summary.py` | `parte1_resumo.csv` | §7.1 (Tab. de status) |
| **Parte II** – BFS, DFS, Eulerianidade, Dijkstra, Bellman-Ford, Floyd-Warshall, Tarjan, Prim/Kruskal | `src/algorithms/` (testes em `tests/`) | `parte2_resultados.csv` | §7.2 |
| Parte II – complexidade teórica e observada; média, desvio e IC (Z ou t-Student) | `src/benchmark.py` | `parte2_tempos.csv`, `parte2_escala.csv`, `parte2_expoentes.csv`, `parte2_ajuste_vertices_arestas.csv`, `tempos_algoritmos.png`, `escala_algoritmos.png` | §6, §7.2 |
| **Parte III.1** – small-world, sem bibliotecas prontas | `src/smallworld.py` | `parte3_smallworld*.csv` (ER e graus preservados) | §7.3.1 |
| Parte III.2 – lei de potência (histograma, CCDF log-log) | `src/powerlaw.py` | `parte3_powerlaw*.csv`, `lei_de_potencia.png` | §7.3.2 |
| Parte III.3 – robustez: remoção aleatória de 5% e dos 5% mais centrais (métricas A–D, boxplot) | `src/centrality.py`, `src/robustness.py` | `parte3_robustez*.csv`, `robustez.png` | §7.3.3 |
| Parte III.4 – descoberta mais interessante | `src/hubs.py` | `parte3_hubs*.csv` | §7.3.4 |
| Parte III.5 (extra) – modelos ER, BA e WS | `src/models.py` | `parte3_modelos.csv`, `modelos_ccdf.png` | §7.3.5 |
| Repositório: códigos, dados tratados, README | `src/`, `scripts/` | `data/processed/`, este README | §3 |
| Relatório no template WebMedia, PDF com a matrícula | `relatorio/` (`main.tex`, `webmedia.cls`) | [`relatorio/224216275.pdf`](relatorio/224216275.pdf) | — |
| Tabelas e números do relatório sem digitação manual | `src/report_tables.py` | `results/latex/tab_*.tex`, `results/latex/numeros.tex` | todo o texto |

## Resumo dos resultados

- **Tratamento:** remoção de 1.089 auto-loops, conversão para não dirigido simples
  (364.481 arestas) e maior componente conexa (LCC): **224.832 vértices e 339.925 arestas**.
  Pesos derivados da reciprocidade: 1 se o par trocou e-mail nos dois sentidos, 2 se não.
- **Parte I (exata):** diâmetro 14, raio 7, comprimento médio 4,118, clusterização 0,079,
  267.313 triângulos; 84% dos vértices têm grau 1 e o maior grau é 7.636.
- **Parte II:** todos os algoritmos foram implementados, validados contra o NetworkX e
  medidos com IC 95%; o estudo de escala compara o tempo com a complexidade teórica.
- **Parte III:** small-world (σ ≈ 2,7×10⁴ contra o Erdős–Rényi, mas só 2,1 com os graus
  preservados); cauda pesada, só aproximadamente uma lei de potência; robusta à remoção
  aleatória de 5% (90,7% na maior componente), mas colapsa ao remover os 5% mais centrais
  (maior componente com 6, 3 e 11 vértices por grau, PageRank e betweenness).
- **Descoberta:** os maiores hubs recebem de milhares de endereços e escrevem para poucos;
  nenhum modelo clássico (ER, BA, WS) reproduz a rede.

O relatório é gerado a partir de `relatorio/` (`main.tex`, `referencias.bib`, `webmedia.cls`).
`python -m src.report_tables` gera as tabelas (`tab_*.tex`) e as macros com os números do
texto (`numeros.tex`) a partir dos CSVs, então nada é digitado à mão.
