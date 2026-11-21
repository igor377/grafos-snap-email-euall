"""Parte I: tabela-resumo "computado / aproximado / não computado" (exigida no enunciado).

Consolida os CSVs gerados por src.metrics, src.distances, src.clustering e
src.visualize em results/tables/parte1_resumo.csv.

Uso:
    python -m src.part1_summary
"""

import pandas as pd

from src.load import TABLES_DIR


def main() -> None:
    b = pd.read_csv(TABLES_DIR / "parte1_basicas.csv").set_index("metrica")
    dr = pd.read_csv(TABLES_DIR / "parte1_diametro_raio.csv").iloc[0]
    paths = pd.read_csv(TABLES_DIR / "parte1_caminhos_amostragem.csv").set_index("k").loc[500]
    cl = pd.read_csv(TABLES_DIR / "parte1_clusterizacao.csv").set_index("escopo")

    def both(key, fmt="{:.0f}"):
        return fmt.format(b.loc[key, "grafo_completo"]), fmt.format(b.loc[key, "lcc"])

    exact = "Computado (exato)"
    rows = [
        ("Número de vértices", *both("vertices"), exact, "Contagem"),
        ("Número de arestas", *both("arestas"), exact, "Contagem (não dirigido simples)"),
        ("Grau mínimo", *both("grau_min"), exact, "Lista de adjacência"),
        ("Grau máximo", *both("grau_max"), exact, "Lista de adjacência"),
        ("Grau médio", *both("grau_medio", "{:.4f}"), exact, "2m/n"),
        ("Distribuição de graus", "-", "ver figura", exact,
         "distribuicao_graus.csv / distribuicao_graus.png"),
        ("Densidade", *both("densidade", "{:.3e}"), exact, "2m / (n(n-1))"),
        ("Número de componentes conexas", *both("componentes"), exact, "BFS"),
        ("Tamanho de cada componente", "ver tabela", "-", exact,
         "componentes_tamanhos.csv / componentes_frequencia.csv"),
        ("Diâmetro", "∞ (desconexo)", str(dr["diametro_lo"]),
         exact if dr["exato"] else "Aproximado (limites)",
         f"BoundingDiameters (Takes & Kosters, 2011), {dr['bfs']} BFS; "
         "no grafo completo é infinito por ser desconexo"),
        ("Raio", "∞ (desconexo)", str(dr["raio_lo"]),
         exact if dr["exato"] else "Aproximado (limites)",
         f"BoundingDiameters, {dr['bfs']} BFS"),
        ("Comprimento médio dos caminhos", "-",
         f"{paths['L_medio']:.4f} [IC95%: {paths['L_ic95_inf']:.4f}; {paths['L_ic95_sup']:.4f}]",
         "Aproximado (amostragem)",
         "BFS de 500 fontes aleatórias; o exato exige V BFS ≈ 1,3×10^11 operações"),
        ("Coeficiente de clusterização médio",
         f"{cl.loc['grafo_completo', 'clusterizacao_media']:.4f}",
         f"{cl.loc['lcc', 'clusterizacao_media']:.4f}", exact, "Contagem de triângulos por vértice"),
        ("Número de triângulos", str(cl.loc["grafo_completo", "triangulos"]),
         str(cl.loc["lcc", "triangulos"]), exact, "Algoritmo forward, O(m^1.5)"),
        ("Visualização", "-", "amostra de 300 vértices", "Computado (amostra)",
         "visualizacao_amostra.png; o grafo completo é ilegível"),
    ]
    df = pd.DataFrame(rows, columns=["medida", "grafo_completo", "lcc", "status", "metodo"])
    df.to_csv(TABLES_DIR / "parte1_resumo.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
