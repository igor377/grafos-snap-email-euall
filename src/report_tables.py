"""Gera as tabelas LaTeX do relatório a partir dos CSVs de results/tables/.

Cada tabela vira um arquivo `results/latex/tab_<nome>.tex` com o ambiente
`table`/`table*` completo (legenda e rótulo), pronto para `\\input`. Assim
nenhum número das tabelas do relatório é transcrito à mão. Se a pasta
`relatorio/` existir, as tabelas são copiadas para `relatorio/tabelas/` e as
figuras PDF/PNG para `relatorio/figuras/`.

Uso:
    python -m src.report_tables
"""

import math
import re
import shutil

import pandas as pd

from src.load import FIGURES_DIR, ROOT, TABLES_DIR

LATEX_DIR = ROOT / "results" / "latex"
REPORT_DIR = ROOT / "relatorio"


# ---------------------------------------------------------------- formatação pt-BR
def _swap(s: str) -> str:
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def inteiro(x) -> str:
    return _swap(f"{int(round(float(x))):,}")


def dec(x, nd: int = 2) -> str:
    return _swap(f"{float(x):,.{nd}f}")


def sci(x, nd: int = 2) -> str:
    """Notação científica em modo matemático: $1{,}04\\times10^{-5}$."""
    x = float(x)
    if x == 0:
        return "0"
    e = math.floor(math.log10(abs(x)))
    m = x / 10 ** e
    return f"${dec(m, nd).replace(',', '{,}')}\\times10^{{{e}}}$"


def num(x, nd: int = 3) -> str:
    """Escolhe automaticamente entre inteiro, decimal e científico."""
    x = float(x)
    if x == int(x) and abs(x) >= 1:
        return inteiro(x)
    if x != 0 and (abs(x) < 10 ** -nd or abs(x) >= 1e6):
        return sci(x)
    return dec(x, nd)


def tex_text(s: str) -> str:
    """Escapa texto livre vindo dos CSVs e formata inteiros longos (224832 -> 224.832)."""
    s = str(s)
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"),
                 ("#", r"\#"), ("×", r"$\times$"), ("≠", r"$\neq$"), ("≥", r"$\geq$"),
                 ("≤", r"$\leq$"), ("γ", r"$\gamma$"), ("σ", r"$\sigma$"),
                 ("=False", ": não"), ("=True", ": sim")):
        s = s.replace(a, b)
    return re.sub(r"(?<![\d.,])\d{4,}(?![\d,])", lambda m: inteiro(m.group()), s)


def table(name: str, caption: str, colspec: str, header: list[str], rows: list[list[str]],
          wide: bool = False, resize: bool = False) -> str:
    env = "table*" if wide else "table"
    width = r"\textwidth" if wide else r"\columnwidth"
    body = [r"\toprule", " & ".join(header) + r" \\", r"\midrule"]
    body += [" & ".join(r) + r" \\" for r in rows]
    body.append(r"\bottomrule")
    tabular = "\n".join([rf"\begin{{tabular}}{{{colspec}}}", *("  " + b for b in body),
                         r"\end{tabular}"])
    if resize:
        tabular = rf"\resizebox{{{width}}}{{!}}{{%" + "\n" + tabular + "}"
    else:
        tabular = r"\small" + "\n" + tabular
    out = "\n".join([f"% Gerado por src/report_tables.py a partir de results/tables/ -- não editar",
                     rf"\begin{{{env}}}[t]", rf"  \caption{{{caption}}}",
                     rf"  \label{{tab:{name}}}", tabular, rf"\end{{{env}}}", ""])
    (LATEX_DIR / f"tab_{name}.tex").write_text(out, encoding="utf-8", newline="\n")
    return out


def csv(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLES_DIR / f"{name}.csv")


# ---------------------------------------------------------------- tabelas
def tab_tratamento():
    t = csv("tratamento_evolucao")
    nomes = {"Grafo bruto (dirigido)": "Grafo bruto (dirigido)",
             "Após remoção de auto-loops (dirigido)": "Sem auto-loops (dirigido)",
             "Após conversão para não dirigido simples": "Não dirigido simples",
             "Maior componente conexa (LCC)": "Maior componente conexa (LCC)"}
    rows = [[nomes.get(r.etapa, r.etapa), inteiro(r.vertices), inteiro(r.arestas)]
            for r in t.itertuples()]
    table("tratamento", "Evolução do grafo ao longo do tratamento.", "lrr",
          ["Etapa", "Vértices", "Arestas"], rows)


def tab_parte1():
    b = csv("parte1_basicas").set_index("metrica")
    dr = csv("parte1_diametro_raio").iloc[0]
    p = csv("parte1_caminhos_amostragem").set_index("k").loc[500]
    c = csv("parte1_clusterizacao").set_index("escopo")
    g, l = "grafo_completo", "lcc"

    def both(key, f):
        return [f(b.loc[key, g]), f(b.loc[key, l])]

    rows = [
        ["Vértices", *both("vertices", inteiro)],
        ["Arestas", *both("arestas", inteiro)],
        ["Grau mínimo", *both("grau_min", inteiro)],
        ["Grau máximo", *both("grau_max", inteiro)],
        ["Grau médio", *both("grau_medio", lambda x: dec(x, 3))],
        ["Densidade", *both("densidade", sci)],
        ["Componentes conexas", *both("componentes", inteiro)],
        ["Maior / menor componente",
         f"{inteiro(b.loc['maior_componente', g])} / {inteiro(b.loc['menor_componente', g])}",
         "--"],
        ["Diâmetro", r"$\infty$ (desconexo)", inteiro(dr["diametro_lo"])],
        ["Raio", r"$\infty$ (desconexo)", inteiro(dr["raio_lo"])],
        ["Comprimento médio $L$", "--", dec(p["L_medio"], 3)],
        ["Clusterização média $C$", dec(c.loc[g, "clusterizacao_media"], 4),
         dec(c.loc[l, "clusterizacao_media"], 4)],
        ["Transitividade", dec(c.loc[g, "transitividade"], 4), dec(c.loc[l, "transitividade"], 4)],
        ["Triângulos", inteiro(c.loc[g, "triangulos"]), inteiro(c.loc[l, "triangulos"])],
    ]
    table("parte1", "Métricas estruturais (grafo não dirigido simples).", "lrr",
          ["Métrica", "Grafo completo", "LCC"], rows)


def tab_status():
    dr = csv("parte1_diametro_raio").iloc[0]
    n_comp = csv("parte1_basicas").set_index("metrica").loc["componentes", "grafo_completo"]
    exato = "Computado (exato)" if dr["exato"] else "Aproximado (limites)"
    rows = [
        ["Vértices, arestas, graus, densidade", "Computado (exato)",
         "Contagem na lista de adjacência"],
        ["Distribuição de graus", "Computado (exato)",
         r"Frequência de cada grau (Figura~\ref{fig:graus})"],
        ["Componentes e tamanho de cada uma", "Computado (exato)",
         f"BFS; tamanhos das {inteiro(n_comp)} componentes no repositório"],
        ["Diâmetro e raio", exato,
         rf"\emph{{BoundingDiameters}}~\cite{{takes2011}}, {inteiro(dr['bfs'])} BFS; "
         "infinitos no grafo completo (desconexo)"],
        ["Comprimento médio dos caminhos", "Aproximado (amostragem)",
         r"BFS a partir de 500 fontes; o exato exigiria $\approx1{,}3\times10^{11}$ operações"],
        ["Clusterização média e triângulos", "Computado (exato)",
         r"Algoritmo \emph{forward}~\cite{schank2005}"],
        ["Visualização", "Computado (amostra)",
         "300 vértices em torno dos 5 maiores hubs; o grafo inteiro é ilegível"],
    ]
    table("status", "Status de cada medida da Parte I: computada exatamente, aproximada ou "
          "não computada.", "p{4.3cm}p{3.1cm}p{9.2cm}",
          ["Medida", "Status", r"Método / justificativa"], rows, wide=True)


def tab_algoritmos():
    t = csv("parte2_tempos")
    res = csv("parte2_resultados").set_index("algoritmo")["resultado"]
    grafo = {"LCC": "LCC", "LCC ponderada": "LCC ponderada", "G_dir": r"$G_{dir}$",
             "subgrafo 300": "subgrafo 300"}
    cplx = {"O(V+E)": "$O(V+E)$", "O((V+E) log V)": r"$O((V+E)\log V)$",
            "O(V·E)": r"$O(V\cdot E)$", "O(V³)": "$O(V^3)$", "O(E log V)": r"$O(E\log V)$"}
    rows = []
    for r in t.itertuples():
        mark = "*" if r.distribuicao != "Normal (Z)" else ""
        rows.append([tex_text(r.algoritmo) + mark, grafo.get(r.grafo, tex_text(r.grafo)),
                     cplx.get(r.complexidade, tex_text(r.complexidade)), dec(r.media_s, 4),
                     dec(r.desvio_s, 4), f"[{dec(r.ic95_inf_s, 4)}; {dec(r.ic95_sup_s, 4)}]",
                     tex_text(res[r.algoritmo])])
    n_z = int(t.loc[t["distribuicao"] == "Normal (Z)", "n"].iloc[0])
    t_rows = t[t["distribuicao"] != "Normal (Z)"]
    note = (f", exceto onde indicado com * (t-Student, $n={int(t_rows['n'].iloc[0])}$)"
            if len(t_rows) else "")
    table("algoritmos", "Algoritmos: complexidade teórica, tempo observado e resultado. "
          f"IC 95\\% pela Normal ($n={n_z}$){note}.", "llllrrl",
          ["Algoritmo", "Grafo", "Complexidade", "Média (s)", "Desvio (s)", r"IC 95\% (s)",
           "Resultado"], rows, wide=True, resize=True)


def tab_escala():
    e = csv("parte2_expoentes")
    rows = []
    for r in e.itertuples():
        row = [r.algoritmo, inteiro(r.expoente_teorico), dec(r.expoente_observado, 2),
               dec(r.R2, 3)]
        if "expoente_vs_f" in e:
            fn = {"V+E": "$V+E$", "(V+E) log V": r"$(V+E)\log V$", "V³": "$V^3$"}
            row += [fn.get(r.funcao_teorica, tex_text(r.funcao_teorica)),
                    dec(r.expoente_vs_f, 2), dec(r.R2_vs_f, 3)]
        rows.append(row)
    header = ["Algoritmo", "Teórico", "Observado", "$R^2$"]
    spec = "lrrr"
    if "expoente_vs_f" in e:
        header += ["$f(n)$", r"Exp. vs.\ $f$", "$R^2$"]
        spec += "lrr"
    table("escala", "Complexidade observada: inclinação em log-log do tempo médio contra o "
          "tamanho da entrada e contra a função teórica $f(n)$ (ideal: 1).", spec, header,
          rows, resize=True)


def tab_smallworld():
    s = csv("parte3_smallworld")
    L, C, sig = s.iloc[0], s.iloc[1], s.iloc[2]
    rows = [
        ["$L$", dec(L.real, 3), dec(L.er_medido, 3), dec(L.er_analitico, 3)],
        ["$C$", dec(C.real, 4), sci(C.er_medido, 1), sci(C.er_analitico, 1)],
        ["$C/C_{rand}$", "--", r"$\approx$ " + inteiro(C.real / C.er_medido),
         r"$\approx$ " + inteiro(C.real / C.er_analitico)],
        ["$L/L_{rand}$", "--", dec(L.real / L.er_medido, 3), dec(L.real / L.er_analitico, 3)],
        [r"$\sigma$", "--", r"$\approx$ " + inteiro(sig.real), r"$\approx$ " + inteiro(sig.er_analitico)],
    ]
    n_er = len(csv("parte3_smallworld_er"))
    table("smallworld", "Small-world: grafo real (LCC) contra Erd\\H{o}s--Rényi equivalente "
          f"(média de {n_er} realizações) e valores analíticos.", "lrrr",
          ["Métrica", "Real", "ER medido", "ER analítico"], rows)


def tab_powerlaw():
    p = csv("parte3_powerlaw")
    nomes = ["Regressão $P(k)$, log-binning", "Regressão na CCDF"]
    rows = []
    for i, r in enumerate(p.itertuples()):
        if i < 2:
            rows.append([nomes[i], dec(r.gamma, 2), f"$R^2 = {dec(r.R2, 3).replace(',', '{,}')}$"])
        else:
            m = re.search(r"k ≥ (\d+) \((\d+) vértices\); KS = ([\d.]+)", r.observacao)
            kmin, ncauda, ks = m.groups()
            parte = "cabeça" if i == 2 else "cauda"
            obs = f"KS = {dec(ks, 3)}" + (f"; {inteiro(ncauda)} vértices" if i > 2 else "")
            rows.append([f"MLE, $k_{{min}}={kmin}$ ({parte})", dec(r.gamma, 2), obs])
    table("powerlaw", r"Estimativas do expoente $\gamma$ de $P(k)\sim k^{-\gamma}$ (LCC).",
          "lrl", ["Método", r"$\gamma$", "Observação"], rows, resize=True)


def tab_robustez():
    s = csv("parte3_robustez").set_index("metrica")
    targets = [c for c in s.columns if c.startswith("direcionada_")]
    tnames = {"direcionada_grau": "Grau", "direcionada_pagerank": "PageRank"}
    labels = {"A_fracao_maior_componente": "A: $S/N$", "B_num_componentes": "B: componentes",
              "C_caminho_medio": "C: $L$ (maior comp.)", "D_fracao_isolados": "D: isolados"}
    fmt = {"A_fracao_maior_componente": lambda x: num(x, 3),
           "B_num_componentes": inteiro, "C_caminho_medio": lambda x: dec(x, 2),
           "D_fracao_isolados": lambda x: num(x, 3)}
    rows = []
    for key, label in labels.items():
        r = s.loc[key]
        f = fmt[key]
        pm = (f"${f(r.aleatoria_media).replace(',', '{,}')} \\pm "
              f"{f(r.aleatoria_desvio).replace(',', '{,}')}$")
        rows.append([label, f(r.original), pm, *(f(r[t]) for t in targets)])
    reps = len(csv("parte3_robustez_aleatoria"))
    table("robustez", "Robustez após remover 5\\% dos vértices (média $\\pm$ desvio em "
          f"{reps} repetições na remoção aleatória; ataques com ranking fixo).",
          "lrr" + "r" * len(targets),
          ["Métrica", "Original", "Aleatória", *(f"Ataque: {tnames.get(t, t)}" for t in targets)],
          rows, resize=True)


def main() -> None:
    LATEX_DIR.mkdir(parents=True, exist_ok=True)
    for fn in (tab_tratamento, tab_parte1, tab_status, tab_algoritmos, tab_escala,
               tab_smallworld, tab_powerlaw, tab_robustez):
        fn()
    files = sorted(LATEX_DIR.glob("tab_*.tex"))
    print("Tabelas geradas:", ", ".join(f.name for f in files))
    if REPORT_DIR.exists():
        (REPORT_DIR / "tabelas").mkdir(exist_ok=True)
        (REPORT_DIR / "figuras").mkdir(exist_ok=True)
        for f in files:
            shutil.copy2(f, REPORT_DIR / "tabelas" / f.name)
        for f in list(FIGURES_DIR.glob("*.pdf")) + list(FIGURES_DIR.glob("*.png")):
            shutil.copy2(f, REPORT_DIR / "figuras" / f.name)
        print(f"Copiadas para {REPORT_DIR / 'tabelas'} e {REPORT_DIR / 'figuras'}")


if __name__ == "__main__":
    main()
