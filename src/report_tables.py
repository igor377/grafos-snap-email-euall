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

from src.load import FIGURES_DIR, ROOT, SUBGRAPH_FILE as SUBGRAPH, TABLES_DIR

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
                 ("=False", ": não"), ("=True", ": sim"), ("–", "--"), ("ő", r"\H{o}")):
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
        ["Comprimento médio $L$", "--", dec(csv("parte1_caminho_exato")["L_exato"].iloc[0], 4)],
        ["Clusterização média $C$", dec(c.loc[g, "clusterizacao_media"], 4),
         dec(c.loc[l, "clusterizacao_media"], 4)],
        ["Transitividade", dec(c.loc[g, "transitividade"], 4), dec(c.loc[l, "transitividade"], 4)],
        ["Triângulos", inteiro(c.loc[g, "triangulos"]), inteiro(c.loc[l, "triangulos"])],
    ]
    table("parte1", "Métricas estruturais (grafo não dirigido simples).", "lrr",
          ["Métrica", "Grafo completo", "LCC"], rows)


def tab_status():
    dr = csv("parte1_diametro_raio").iloc[0]
    ex = csv("parte1_caminho_exato").iloc[0]
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
        ["Comprimento médio dos caminhos", "Computado (exato)",
         f"BFS a partir dos {inteiro(ex['bfs_executadas'])} vértices não folha; a soma das "
         f"{inteiro(ex['folhas_deduzidas'])} folhas é deduzida da do seu vizinho"],
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
        if r.algoritmo == "Bellman-Ford":
            # maior subgrafo do estudo de escala, para não ficar só com os 300 vértices
            esc = csv("parte2_escala")
            b = esc[esc["algoritmo"] == "Bellman-Ford"].sort_values("V").iloc[-1]
            rows.append([tex_text(r.algoritmo) + ("*" if b.distribuicao != "Normal (Z)" else ""),
                         f"subgrafo {inteiro(b.V)}",
                         cplx.get(r.complexidade, tex_text(r.complexidade)), dec(b.media_s, 4),
                         dec(b.desvio_s, 4),
                         f"[{dec(b.ic95_inf_s, 4)}; {dec(b.ic95_sup_s, 4)}]",
                         f"{inteiro(b.E)} arestas; {int(b.rodadas)} rodadas"])
    z_rows = t[t["distribuicao"] == "Normal (Z)"]
    t_rows = t[t["distribuicao"] != "Normal (Z)"]
    if len(z_rows):
        note = f"IC 95\\% pela Normal ($n={int(z_rows['n'].iloc[0])}$)"
        if len(t_rows):
            note += f", exceto onde indicado com * (t-Student, $n={int(t_rows['n'].iloc[0])}$)"
    else:  # execução reduzida (--quick): todas as medições com n < 30
        note = "IC 95\\% pela t-Student (*), execução reduzida"
    table("algoritmos", "Algoritmos: complexidade teórica, tempo observado e resultado. "
          f"{note}.", "llllrrl",
          ["Algoritmo", "Grafo", "Complexidade", "Média (s)", "Desvio (s)", r"IC 95\% (s)",
           "Resultado"], rows, wide=True, resize=True)


def tab_escala():
    e = csv("parte2_expoentes")
    exp_v = csv("parte2_ajuste_vertices_arestas").set_index("algoritmo")["expoente_vs_V"]
    reps = int(csv("parte2_escala")["n"].iloc[0])
    fn = {"V+E": "$V+E$", "(V+E) log V": r"$(V+E)\log V$", "E log V": r"$E\log V$",
          "V·E": r"$V\cdot E$", "V³": "$V^3$"}
    rows = []
    for r in e.itertuples():
        obs = ""
        if "rodadas_min" in e and pd.notna(r.rodadas_min):
            obs = f"{int(r.rodadas_min)} a {int(r.rodadas_max)} rodadas (parada antecipada)"
        rows.append([tex_text(r.algoritmo), fn.get(r.funcao_teorica, tex_text(r.funcao_teorica)),
                     dec(r.expoente_vs_f, 2),
                     dec(exp_v[r.algoritmo], 2) if r.algoritmo in exp_v else "--",
                     dec(r.R2_vs_f, 3), f"{inteiro(r.V_min)}--{inteiro(r.V_max)}", obs])
    table("escala", "Complexidade observada: inclinação em log-log do tempo médio contra a "
          f"função teórica $f(n)$ (ideal: 1) e, nos lineares e quase lineares, contra $V$, "
          f"com {reps} repetições por tamanho.",
          "llrrrrl", ["Algoritmo", "$f(n)$", "Incl. $f(n)$", "Incl. $V$", "$R^2$",
                      r"Vértices", "Observação"],
          rows, resize=True)


def tab_smallworld():
    s = csv("parte3_smallworld")
    L, C, sig = s.iloc[0], s.iloc[1], s.iloc[2]
    rows = [
        ["$L$", dec(L.real, 3), dec(L.er_medido, 3), dec(L.er_analitico, 3),
         dec(L.config_medido, 3)],
        ["$C$", dec(C.real, 4), sci(C.er_medido, 1), sci(C.er_analitico, 1),
         dec(C.config_medido, 4)],
        ["$C/C_{nulo}$", "--", r"$\approx$ " + inteiro(C.real / C.er_medido),
         r"$\approx$ " + inteiro(C.real / C.er_analitico), dec(C.real / C.config_medido, 2)],
        ["$L/L_{nulo}$", "--", dec(L.real / L.er_medido, 3), dec(L.real / L.er_analitico, 3),
         dec(L.real / L.config_medido, 3)],
        [r"$\sigma$", "--", r"$\approx$ " + inteiro(sig.real),
         r"$\approx$ " + inteiro(sig.er_analitico), dec(sig.config_medido, 2)],
    ]
    n_er = len(csv("parte3_smallworld_er"))
    n_cf = len(csv("parte3_smallworld_config"))
    table("smallworld", "Small-world: grafo real (LCC, $L$ exato) contra dois modelos nulos: "
          f"Erd\\H{{o}}s--Rényi equivalente (média de {n_er} realizações, e valores "
          f"analíticos) e reconexão que preserva os graus (média de {n_cf} realizações).",
          "lrrrr", ["Métrica", "Real", "ER medido", "ER analítico", "Graus preservados"],
          rows, resize=True)


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
    tnames = {"direcionada_grau": "Grau", "direcionada_pagerank": "PageRank",
              "direcionada_betweenness": "Betweenness"}
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
          f"{reps} repetições na remoção aleatória; ataques com ranking fixo). "
          "Em C, o original é o $L$ exato; após a remoção, $L$ é estimado com 50 fontes.",
          "lrr" + "r" * len(targets),
          ["Métrica", "Original", "Aleatória", *(f"Ataque: {tnames.get(t, t)}" for t in targets)],
          rows, resize=True)


def tab_hubs():
    h = csv("parte3_hubs")
    rows = [[inteiro(r.posicao_grau), inteiro(r.grau), inteiro(r.remetentes_entrada),
             inteiro(r.destinatarios_saida), dec(100 * r.frac_vizinhos_folha, 2) + r"\%",
             inteiro(r.pos_pagerank), inteiro(r.pos_betweenness)]
            for r in h.itertuples()]
    table("hubs", "Os 10 maiores hubs da LCC: endereços distintos dos quais recebeu e para os "
          "quais enviou e-mail, fração de vizinhos que são folhas (grau 1) e posição nos "
          "rankings de PageRank e betweenness.", "rrrrrrr",
          ["Pos.", "Grau", "Remetentes", "Destinatários", "Folhas", "PageRank", "Betweenness"],
          rows, resize=True)


def tab_modelos():
    m = csv("parte3_modelos")
    names = {"email-EuAll (LCC)": r"\texttt{email-EuAll} (LCC)"}
    rows = []
    for r in m.itertuples():
        gamma = "--" if pd.isna(r.gamma_mle) else (
            f"{dec(r.gamma_mle, 2)} (KS {dec(r.ks_mle, 3)})")
        rows.append([names.get(r.modelo, tex_text(r.modelo).replace("p=0.1", "p=0,1")),
                     inteiro(r.m), inteiro(r.grau_max), dec(100 * r.fracao_grau1, 1) + r"\%",
                     num(r.C, 4), dec(r.L, 2), gamma])
    table("modelos", "Grafo real contra modelos clássicos gerados por código próprio com o "
          "mesmo número de vértices ($L$ estimado por BFS de 100 fontes; $\\gamma$ por "
          "máxima verossimilhança na cauda, com o KS do ajuste).", "lrrrrrl",
          ["Grafo", "Arestas", "Grau máx.", "Grau 1", "$C$", "$L$", r"$\gamma$ (KS)"],
          rows, wide=True, resize=True)


def numeros_extras(n_lcc) -> dict[str, str]:
    """Demais números do texto que vêm dos dados (componentes, resultados dos algoritmos,
    lei de potência, robustez e modelos clássicos)."""
    tam = csv("componentes_tamanhos")["tamanho"].tolist()
    freq = csv("componentes_frequencia").set_index("tamanho")["quantidade"]
    cl = csv("parte1_clusterizacao").set_index("escopo")
    b = csv("parte1_basicas").set_index("metrica")
    res = csv("parte2_resultados").set_index("algoritmo")["resultado"]
    er = csv("parte3_smallworld_er")
    pl = csv("parte3_powerlaw")
    sens = csv("parte3_powerlaw_sensibilidade")
    tail = sens[sens["kmin"] >= 5]
    rb = csv("parte3_robustez").set_index("metrica")
    hr = csv("parte3_hubs_resumo").iloc[0]
    md = csv("parte3_modelos").set_index("modelo")
    ba = md.loc[[i for i in md.index if i.startswith("Barab")][0]]
    ws = md.loc[[i for i in md.index if i.startswith("Watts")][0]]
    erm = md.loc[[i for i in md.index if i.startswith("Erd")][0]]
    real = md.loc["email-EuAll (LCC)"]

    def grab(alg, pat):
        return int(re.search(pat, res[alg]).group(1))

    D = "D_fracao_isolados"
    targets = [c for c in rb.columns if c.startswith("direcionada_")]
    return {
        "nTestes": inteiro(count_tests()),
        "nVLccMenosUm": inteiro(n_lcc - 1), "nArcos": inteiro(2 * b.loc["arestas", "lcc"]),
        "grauMedioLccTres": dec(b.loc["grau_medio", "lcc"], 3),
        "pctDescartado": dec(100 - 100 * n_lcc / b.loc["vertices", "grafo_completo"], 1),
        "nESub": inteiro(sum(1 for _ in open_lines(SUBGRAPH))),
        "nIsolados": inteiro(freq.loc[1]), "compPares": inteiro(freq.loc[2]),
        "compSegunda": inteiro(tam[1]), "compTerceira": inteiro(tam[2]),
        "verticesTriangulos": inteiro(cl.loc["lcc", "vertices_em_triangulos"]),
        "grauImpar": inteiro(grab("Eulerianidade (não dirigido)", r"(\d+) vértices de grau ímpar")),
        "desbalanceados": inteiro(grab("Eulerianidade (dirigido)", r"(\d+) vértices com")),
        "nScc": inteiro(grab("Tarjan (SCC)", r"(\d+) SCCs")),
        "maiorScc": inteiro(grab("Tarjan (SCC)", r"maior com (\d+)")),
        "pctMaiorScc": dec(100 * grab("Tarjan (SCC)", r"maior com (\d+)") / n_lcc
                           * n_lcc / b.loc["vertices", "grafo_completo"], 1),
        "pontes": inteiro(grab("Tarjan (pontes/articulações)", r"(\d+) pontes")),
        "articulacoes": inteiro(grab("Tarjan (pontes/articulações)", r"(\d+) articula")),
        "pctGiganteER": dec(100 * er["fracao_maior_componente"].mean(), 1),
        "Rbins": dec(pl["R2"].iloc[0], 2),
        "gammaSensMax": dec(sens["gamma_mle"].max(), 2),
        "gammaSensMin": dec(sens["gamma_mle"].min(), 2),
        "ksCaudaMin": dec(tail["ks"].min(), 2), "ksCaudaMax": dec(tail["ks"].max(), 2),
        "rRemovidos": inteiro(math.ceil(0.05 * n_lcc)),
        "Loriginal": dec(rb.loc["C_caminho_medio", "original"], 2),
        "Laleatoria": dec(rb.loc["C_caminho_medio", "aleatoria_media"], 2),
        "LaleatoriaDesvio": dec(rb.loc["C_caminho_medio", "aleatoria_desvio"], 2),
        "LoriginalEst": dec(rb.loc["C_caminho_medio", "original_estimado"], 2),
        "pctIsolAleat": dec(100 * rb.loc[D, "aleatoria_media"], 1),
        "BdesvioAleat": inteiro(round(rb.loc["B_num_componentes", "aleatoria_desvio"], -2)),
        "compAtaqueGrau": inteiro(rb.loc["B_num_componentes", "direcionada_grau"]),
        "pctIsolGrau": dec(100 * rb.loc[D, "direcionada_grau"], 1),
        "pctIsolMin": dec(math.floor(1000 * min(rb.loc[D, c] for c in targets)) / 10, 1),
        "folhasTopDez": inteiro(hr["folhas_ligadas_aos_top10"]),
        "folhasMinTopNove": dec(100 * csv("parte3_hubs")["frac_vizinhos_folha"].head(9).min(), 0),
        "kmaxER": inteiro(erm["grau_max"]), "kmaxBA": inteiro(ba["grau_max"]),
        "kmaxWS": inteiro(ws["grau_max"]),
        "Cws": dec(ws["C"], 2), "Lws": dec(ws["L"], 1),
        "gammaBA": dec(ba["gamma_mle"], 2), "ksBA": dec(ba["ks_mle"], 3),
        "razaoCba": inteiro(round(real["C"] / ba["C"], -1)),
        "razaoKmaxBA": inteiro(round(real["grau_max"] / ba["grau_max"])),
    }


def count_tests() -> int:
    """Número de testes da suíte (pytest --collect-only), para citar no texto."""
    import subprocess
    import sys
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8").stdout
    return sum(1 for line in out.splitlines() if "::" in line)


def open_lines(path):
    import gzip
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                yield line


def numeros() -> dict[str, str]:
    """Macros LaTeX (\\newcommand) com os números citados no TEXTO do relatório, lidos
    dos CSVs. Gravadas em results/latex/numeros.tex; o main.tex faz \\input dele."""
    ev = csv("tratamento_evolucao")["arestas"].tolist()
    evv = csv("tratamento_evolucao")["vertices"].tolist()
    b = csv("parte1_basicas").set_index("metrica")
    dr = csv("parte1_diametro_raio").iloc[0]
    ex = csv("parte1_caminho_exato").iloc[0]
    sp = csv("parte1_caminhos_amostragem").set_index("k")
    cl = csv("parte1_clusterizacao").set_index("escopo")
    dg = csv("distribuicao_graus").set_index("grau")
    t = csv("parte2_tempos").set_index("algoritmo")
    res = csv("parte2_resultados").set_index("algoritmo")["resultado"]
    ex2 = csv("parte2_expoentes").set_index("algoritmo")["expoente_vs_f"]
    esc = csv("parte2_escala")
    esc_bf = esc[esc["algoritmo"] == "Bellman-Ford"]
    sw = csv("parte3_smallworld").set_index("metrica")
    pl = csv("parte3_powerlaw")["gamma"].tolist()
    rb = csv("parte3_robustez").set_index("metrica")
    rk = csv("parte3_robustez_rankings").iloc[0]
    hb = csv("parte3_hubs").iloc[0]
    hr = csv("parte3_hubs_resumo").iloc[0]
    n_lcc = b.loc["vertices", "lcc"]

    def first_int(s):
        return int(re.search(r"peso total (\d+)", s).group(1))

    def tsec(name, nd=3):
        return dec(t.loc[name, "media_s"], nd)

    L, C = "Comprimento médio L", "Clusterização média C"
    S = "σ = (C/C_r)/(L/L_r)"
    A = "A_fracao_maior_componente"
    m = {
        # tratamento e Parte I
        "nVBruto": inteiro(evv[0]), "nEBruto": inteiro(ev[0]),
        "nLoops": inteiro(ev[0] - ev[1]), "nEUnd": inteiro(ev[2]),
        "nRecip": inteiro(ev[1] - ev[2]),
        "pctRecip": dec(100 * 2 * (ev[1] - ev[2]) / ev[1], 0),
        "nVLcc": inteiro(n_lcc), "nELcc": inteiro(b.loc["arestas", "lcc"]),
        "pctVLcc": dec(100 * n_lcc / evv[0], 1),
        "pctELcc": dec(100 * b.loc["arestas", "lcc"] / ev[2], 1),
        "nComp": inteiro(b.loc["componentes", "grafo_completo"]),
        "grauMax": inteiro(b.loc["grau_max", "lcc"]),
        "grauMedioLcc": dec(b.loc["grau_medio", "lcc"], 2),
        "pctFolhas": dec(100 * dg.loc[1, "P_k"], 1),
        "diametro": inteiro(dr["diametro_lo"]), "raio": inteiro(dr["raio_lo"]),
        "nBfsDiam": inteiro(dr["bfs"]),
        "Lexato": dec(ex["L_exato"], 3), "nBfsLexato": inteiro(ex["bfs_executadas"]),
        "nFolhasDeduzidas": inteiro(ex["folhas_deduzidas"]),
        "minLexato": dec(ex["tempo_s"] / 60, 0),
        "Lamostra": dec(sp.loc[500, "L_medio"], 3),
        "LamostraInf": dec(sp.loc[500, "L_ic95_inf"], 3),
        "LamostraSup": dec(sp.loc[500, "L_ic95_sup"], 3),
        "Ccompleto": dec(cl.loc["grafo_completo", "clusterizacao_media"], 4),
        "Clcc": dec(cl.loc["lcc", "clusterizacao_media"], 4),
        "transit": dec(cl.loc["lcc", "transitividade"], 4),
        "triangulos": inteiro(cl.loc["lcc", "triangulos"]),
        # Parte II
        "tBfs": tsec("BFS"), "tDijkstra": tsec("Dijkstra (heap)"),
        "razaoDijkstraBfs": dec(t.loc["Dijkstra (heap)", "media_s"] / t.loc["BFS", "media_s"], 1),
        "tFwPuro": dec(t.loc["Floyd-Warshall (Python puro)", "media_s"], 2),
        "tFwNumpy": dec(t.loc["Floyd-Warshall (numpy)", "media_s"], 3),
        "razaoFw": dec(t.loc["Floyd-Warshall (Python puro)", "media_s"]
                       / t.loc["Floyd-Warshall (numpy)", "media_s"], 0),
        "pesoMst": inteiro(first_int(res["Prim (heap)"])),
        # pesos 1 (recíproco) e 2 (mão única): peso = 2(V−1) − nº de arestas recíprocas
        "recipNaArvore": inteiro(2 * (n_lcc - 1) - first_int(res["Prim (heap)"])),
        "kruskalVsPrim": (
            "Kruskal foi mais rápido: a ordenação das arestas é feita em C pelo Python, e o "
            "\\emph{union-find} com compressão de caminho e união por rank tem custo quase "
            "constante."
            if t.loc["Kruskal (union-find)", "media_s"] < t.loc["Prim (heap)", "media_s"]
            else "Prim foi mais rápido neste grafo, apesar da mesma complexidade $O(E\\log V)$."),
        "distMaxDijkstra": re.search(r"dist\. máx\. (\d+)", res["Dijkstra (heap)"]).group(1),
        "rodadasBf": re.search(r"(\d+) rodadas", res["Bellman-Ford"]).group(1),
        "rodadasEscala": (lambda lo, hi: str(lo) if lo == hi else f"{lo} a {hi}")(
            int(esc_bf["rodadas"].min()), int(esc_bf["rodadas"].max())),
        **(lambda ve: {
            "evMaiorEscala": dec(ve["E_por_V_menor_grafo"].iloc[0], 1),
            "evMenorEscala": dec(ve["E_por_V_maior_grafo"].iloc[0], 1),
            "expVMin": dec(ve["expoente_vs_V"].min(), 2),
            "expVMax": dec(ve["expoente_vs_V"].max(), 2),
            "Rnm": dec(math.floor(1000 * ve["R2_aV_bE"].min()) / 1000, 3),
        })(csv("parte2_ajuste_vertices_arestas")),
        "tBfEscala": dec(esc_bf.sort_values("V")["media_s"].iloc[-1], 3),
        "vBfEscala": inteiro(esc_bf["V"].max()),
        "eBfEscala": inteiro(esc_bf.sort_values("V")["E"].iloc[-1]),
        "tFwNumpyMil": dec(esc.query("algoritmo == 'Floyd-Warshall (numpy)'")
                           .sort_values("V")["media_s"].iloc[-1], 1),
        **{f"exp{k}": dec(ex2[v], 2) for k, v in (
            ("Bfs", "BFS"), ("Dfs", "DFS"), ("Euler", "Eulerianidade"),
            ("Tarjan", "Tarjan (pontes/articulações)"), ("Dijkstra", "Dijkstra"),
            ("Prim", "Prim"), ("Kruskal", "Kruskal"), ("Bf", "Bellman-Ford"),
            ("Fw", "Floyd-Warshall"), ("FwNumpy", "Floyd-Warshall (numpy)"))},
        # Parte III
        "Lrand": dec(sw.loc[L, "er_medido"], 1), "Lconf": dec(sw.loc[L, "config_medido"], 2),
        "Crand": sci(sw.loc[C, "er_medido"], 1).strip("$"),
        "Cconf": dec(sw.loc[C, "config_medido"], 4),
        "CsobreCr": inteiro(sw.loc[C, "razao_real_er"]),
        "CsobreCconf": dec(sw.loc[C, "razao_real_config"], 1),
        "sigmaER": sci(sw.loc[S, "real"], 1).strip("$"),
        "sigmaConf": dec(sw.loc[S, "config_medido"], 1),
        "gammaBins": dec(pl[0], 2), "gammaCcdf": dec(pl[1], 2),
        "gammaCabeca": dec(pl[2], 2), "gammaCauda": dec(pl[3], 2),
        "Srand": dec(rb.loc[A, "aleatoria_media"], 3),
        "SrandDesvio": dec(rb.loc[A, "aleatoria_desvio"], 3),
        "pctSrand": dec(100 * rb.loc[A, "aleatoria_media"], 1),
        **{f"maiorComp{k}": inteiro(round(rb.loc[A, f"direcionada_{c}"] * n_lcc))
           for k, c in (("Grau", "grau"), ("Pr", "pagerank"), ("Btw", "betweenness"))},
        "sobrepGrauPr": dec(100 * rk["sobreposicao_grau_pagerank"], 0),
        "sobrepGrauBtw": dec(100 * rk["sobreposicao_grau_betweenness"], 0),
        "sobrepPrBtw": dec(100 * rk["sobreposicao_pagerank_betweenness"], 0),
        "hubRemetentes": inteiro(hb["remetentes_entrada"]),
        "hubDestinatarios": inteiro(hb["destinatarios_saida"]),
        "hubFolhas": dec(100 * hb["frac_vizinhos_folha"], 2),
        "pctFolhasTopDez": dec(100 * hr["fracao_das_folhas_nos_top10"], 0),
    }
    m.update(numeros_extras(n_lcc))
    # "{,}" em vez de "," para o decimal funcionar também dentro de fórmulas ($...$)
    m = {k: (v if "{,}" in v else v.replace(",", "{,}")) for k, v in m.items()}
    lines = ["% Gerado por src/report_tables.py a partir de results/tables/ -- não editar"]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
    (LATEX_DIR / "numeros.tex").write_text("\n".join(lines) + "\n", encoding="utf-8",
                                           newline="\n")
    return m


def main() -> None:
    LATEX_DIR.mkdir(parents=True, exist_ok=True)
    for fn in (tab_tratamento, tab_parte1, tab_status, tab_algoritmos, tab_escala,
               tab_smallworld, tab_powerlaw, tab_robustez, tab_hubs, tab_modelos):
        fn()
    numeros()
    files = sorted(LATEX_DIR.glob("tab_*.tex")) + [LATEX_DIR / "numeros.tex"]
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
