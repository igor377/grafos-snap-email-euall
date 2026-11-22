"""Parte III: perfil dos maiores hubs da LCC (apoio à "descoberta mais interessante").

Para os 10 vértices de maior grau: grau, e-mails enviados/recebidos (graus de saída e
entrada no grafo dirigido), fração dos vizinhos que são folhas (grau 1) e a posição
no ranking de PageRank e de betweenness. Os endereços do email-EuAll são anônimos,
por isso identificamos os hubs pelo id original do SNAP.

Uso (requer `python -m src.centrality`):
    python -m src.hubs
"""

import pandas as pd

from src.centrality import load_centralities
from src.load import TABLES_DIR

TOP = 10


def main() -> None:
    c = load_centralities()
    c["pos_pagerank"] = c["pagerank"].rank(ascending=False, method="min").astype(int)
    c["pos_betweenness"] = c["betweenness"].rank(ascending=False, method="min").astype(int)
    top = c.sort_values(["grau", "id"], ascending=[False, True]).head(TOP)
    out = pd.DataFrame({
        "posicao_grau": range(1, TOP + 1),
        "id_original": top["id_original"].to_numpy(),
        "grau": top["grau"].to_numpy(),
        # grau de saída: nº de endereços DISTINTOS para os quais o hub enviou e-mail;
        # grau de entrada: nº de endereços distintos dos quais recebeu
        "destinatarios_saida": top["grau_saida"].to_numpy(),
        "remetentes_entrada": top["grau_entrada"].to_numpy(),
        "frac_vizinhos_folha": top["frac_vizinhos_grau1"].to_numpy(),
        "pos_pagerank": top["pos_pagerank"].to_numpy(),
        "pos_betweenness": top["pos_betweenness"].to_numpy(),
    })
    out.to_csv(TABLES_DIR / "parte3_hubs.csv", index=False)
    print(out.to_string(index=False))

    # Resumo: quanto do grafo fica pendurado nos hubs
    leaves = (c["grau"] == 1).sum()
    leaves_on_top = top.apply(lambda r: round(r["grau"] * r["frac_vizinhos_grau1"]), axis=1).sum()
    resumo = pd.DataFrame([{
        "folhas_na_lcc": int(leaves),
        "folhas_ligadas_aos_top10": int(leaves_on_top),
        "fracao_das_folhas_nos_top10": leaves_on_top / leaves,
        "top10_com_mais_remetentes_que_destinatarios":
            int((top["grau_saida"] < top["grau_entrada"]).sum()),
    }])
    resumo.to_csv(TABLES_DIR / "parte3_hubs_resumo.csv", index=False)
    print()
    print(resumo.to_string(index=False))


if __name__ == "__main__":
    main()
