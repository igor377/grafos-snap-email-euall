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

> Instruções completas de execução serão adicionadas ao longo do desenvolvimento.
