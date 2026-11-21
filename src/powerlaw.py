"""Parte III.2: a distribuição de graus segue uma lei de potência P(k) ~ k^(-γ)?

Procedimento (Apêndice B):
  1. grau de cada vértice e frequência de cada valor de k (LCC);
  2. histograma P(k) e CCDF P(K ≥ k) em escala log-log;
  3. se for lei de potência: log P(k) = −γ log k + c (reta) e a CCDF também é
     reta, com inclinação −(γ − 1).

Estimativas de γ (implementação própria):
  a) regressão linear em log-log do histograma com log-binning (bins de largura
     logarítmica, que reduzem o ruído da cauda onde a maioria dos k tem 0 ou 1 vértice);
  b) regressão linear em log-log da CCDF: γ = 1 − inclinação;
  c) máxima verossimilhança discreta (Clauset, Shalizi & Newman, 2009): modelo
     zeta P(k) = k^(−γ) / ζ(γ, k_min) para k ≥ k_min, γ obtido maximizando a
     log-verossimilhança numericamente; k_min escolhido minimizando a distância de
     Kolmogorov–Smirnov entre a CCDF empírica e a do modelo.

Uso:
    python -m src.powerlaw
"""

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import zeta as hurwitz_zeta  # ζ(s, q) = Σ_{k≥0} (k + q)^(−s)

from src.load import FIGURES_DIR, TABLES_DIR, load_lcc
from src.metrics import degrees
from src.treatment import build_adjacency


def ccdf(deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Valores distintos de k e P(K ≥ k)."""
    ks, counts = np.unique(deg, return_counts=True)
    tail = np.cumsum(counts[::-1])[::-1] / len(deg)
    return ks, tail


def log_binned_pk(deg: np.ndarray, bins_per_decade: int = 8):
    """P(k) com bins logarítmicos: densidade = contagem / (largura do bin · n)."""
    kmax = deg.max()
    edges = np.unique(np.floor(np.logspace(0, math.log10(kmax + 1),
                                           int(math.log10(kmax + 1) * bins_per_decade) + 2)))
    hist, _ = np.histogram(deg, bins=edges)
    width = np.diff(edges)
    centers = np.sqrt(edges[:-1] * np.maximum(edges[1:] - 1, edges[:-1]))
    density = hist / (width * len(deg))
    mask = hist > 0
    return centers[mask], density[mask]


def fit_line(x, y) -> tuple[float, float, float]:
    """Regressão de log10(y) em log10(x): (inclinação, intercepto, R²)."""
    lx, ly = np.log10(x), np.log10(y)
    slope, intercept = np.polyfit(lx, ly, 1)
    pred = slope * lx + intercept
    r2 = 1 - np.sum((ly - pred) ** 2) / np.sum((ly - ly.mean()) ** 2)
    return float(slope), float(intercept), float(r2)


def mle_gamma(deg: np.ndarray, kmin: int) -> float:
    """MLE discreta exata: maximiza  ℓ(γ) = −n ln ζ(γ, k_min) − γ Σ ln k_i
    (ζ de Hurwitz), por busca de seção áurea em γ ∈ (1, 6)."""
    tail = deg[deg >= kmin]
    n, s = len(tail), float(np.sum(np.log(tail)))

    def neg_loglik(g):
        return n * math.log(hurwitz_zeta(g, kmin)) + g * s

    lo, hi = 1.0001, 6.0
    phi = (math.sqrt(5) - 1) / 2
    a, b = hi - phi * (hi - lo), lo + phi * (hi - lo)
    fa, fb = neg_loglik(a), neg_loglik(b)
    while hi - lo > 1e-6:
        if fa < fb:
            hi, b, fb = b, a, fa
            a = hi - phi * (hi - lo)
            fa = neg_loglik(a)
        else:
            lo, a, fa = a, b, fb
            b = lo + phi * (hi - lo)
            fb = neg_loglik(b)
    return (lo + hi) / 2


def mle_gamma_approx(deg: np.ndarray, kmin: int) -> float:
    """Aproximação fechada de Clauset et al.: γ ≈ 1 + n [Σ ln(k_i/(k_min − 1/2))]^(−1).
    Tem viés para k_min pequeno; mantida apenas para comparação."""
    tail = deg[deg >= kmin]
    return 1 + len(tail) / np.sum(np.log(tail / (kmin - 0.5)))


def ks_distance(deg: np.ndarray, kmin: int, gamma: float) -> float:
    """KS entre a CCDF empírica da cauda e a CCDF discreta exata ζ(γ, k)/ζ(γ, k_min)."""
    tail = np.sort(deg[deg >= kmin])
    ks, emp = ccdf(tail)
    model = hurwitz_zeta(gamma, ks.astype(float)) / hurwitz_zeta(gamma, kmin)
    return float(np.max(np.abs(emp - model)))


def fit_mle(deg: np.ndarray, min_kmin: int = 1, max_kmin: int = 100) -> dict:
    best = None
    for kmin in range(min_kmin, max_kmin + 1):
        if np.sum(deg >= kmin) < 50:
            break
        g = mle_gamma(deg, kmin)
        d = ks_distance(deg, kmin, g)
        if best is None or d < best["ks"]:
            best = {"kmin": kmin, "gamma": g, "ks": d, "n_cauda": int(np.sum(deg >= kmin))}
    n_tail = best["n_cauda"]
    best["gamma_erro_padrao"] = (best["gamma"] - 1) / math.sqrt(n_tail)
    return best


def main() -> None:
    n, edges, _ = load_lcc()
    deg = np.asarray(degrees(build_adjacency(n, edges)))

    xb, yb = log_binned_pk(deg)
    s_b, i_b, r2_b = fit_line(xb, yb)
    ks, tail = ccdf(deg)
    s_c, i_c, r2_c = fit_line(ks, tail)
    mle = fit_mle(deg)                 # k_min livre: o KS escolhe k_min = 1 (cabeça)
    mle_tail = fit_mle(deg, min_kmin=5)  # regime da cauda

    def mle_row(name, r):
        return (name, r["gamma"], None,
                f"k ≥ {r['kmin']} ({r['n_cauda']} vértices); KS = {r['ks']:.4f}; "
                f"erro padrão = {r['gamma_erro_padrao']:.4f}")

    table = pd.DataFrame([
        ("Regressão log-log de P(k) (log-binning)", -s_b, r2_b, "k ≥ 1"),
        ("Regressão log-log da CCDF", 1 - s_c, r2_c, "k ≥ 1"),
        mle_row("MLE discreta, k_min por KS (cabeça)", mle),
        mle_row("MLE discreta, k_min ≥ 5 por KS (cauda)", mle_tail),
    ], columns=["metodo", "gamma", "R2", "observacao"])
    table.to_csv(TABLES_DIR / "parte3_powerlaw.csv", index=False)
    print(table.to_string(index=False))

    # Sensibilidade da MLE ao corte k_min
    sens = []
    for kmin in (1, 2, 3, 5, 10, 20, 50, 100):
        g = mle_gamma(deg, kmin)
        n_tail = int(np.sum(deg >= kmin))
        sens.append({"kmin": kmin, "n_cauda": n_tail, "gamma_mle": g,
                     "erro_padrao": (g - 1) / math.sqrt(n_tail),
                     "ks": ks_distance(deg, kmin, g)})
    sens = pd.DataFrame(sens)
    sens.to_csv(TABLES_DIR / "parte3_powerlaw_sensibilidade.csv", index=False)
    print("\nSensibilidade da MLE a k_min:")
    print(sens.to_string(index=False))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    dist = pd.Series(deg).value_counts().sort_index()
    ax1.scatter(dist.index, dist.values / n, s=6, alpha=0.4, label="P(k) bruto")
    ax1.scatter(xb, yb, s=30, color="C1", label="P(k) com log-binning")
    xx = np.logspace(0, math.log10(deg.max()), 50)
    ax1.plot(xx, 10 ** i_b * xx ** s_b, "--", color="C3",
             label=f"ajuste: γ = {-s_b:.2f} (R² = {r2_b:.3f})")
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlabel("Grau k")
    ax1.set_ylabel("P(k)")
    ax1.set_title("Distribuição de graus (log-log)")
    ax1.grid(True, which="both", alpha=0.3)
    ax1.legend(fontsize=8)

    ax2.scatter(ks, tail, s=8, label="CCDF empírica")
    ax2.plot(xx, 10 ** i_c * xx ** s_c, "--", color="C3",
             label=f"ajuste linear: γ = {1 - s_c:.2f} (R² = {r2_c:.3f})")
    for r, color, label in ((mle, "C2", "MLE cabeça"), (mle_tail, "C4", "MLE cauda")):
        kmin, g = r["kmin"], r["gamma"]
        xm = np.logspace(math.log10(kmin), math.log10(deg.max()), 50)
        frac = r["n_cauda"] / n
        ax2.plot(xm, frac * hurwitz_zeta(g, xm) / hurwitz_zeta(g, kmin), "-", color=color,
                 label=f"{label}: γ = {g:.2f}, k_min = {kmin}")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("Grau k")
    ax2.set_ylabel("P(K ≥ k)")
    ax2.set_ylim(tail.min() / 3, 1.5)
    ax2.set_title("CCDF (log-log)")
    ax2.grid(True, which="both", alpha=0.3)
    ax2.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "lei_de_potencia.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
