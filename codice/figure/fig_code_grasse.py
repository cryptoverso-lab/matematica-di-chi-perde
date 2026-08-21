"""Cap. 9 — Quanto poco somiglia a una campana.

Distribuzione dei rendimenti giornalieri contro la normale con la stessa media
e la stessa deviazione. Le code non sono "un po' piu' spesse": contengono
eventi che il modello a campana considera impossibili.

Il pannello destro mette accanto a Bitcoin una blue chip industriale quotata a
Milano, contando i giorni estremi **ogni mille sedute** — cosi' due serie di
lunghezza molto diversa si confrontano senza barare. Serve a rispondere alla
sola obiezione seria che si puo' fare a questo capitolo: che le code grasse
siano una stranezza delle cripto. Non lo sono.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.layout import figsize  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.metriche import rendimenti  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-09"
SOGLIE = [3, 4, 5, 8]
MERCATI = [("btcusdt", "Bitcoin"), ("eni", "ENI")]
DIDASCALIA = (
    "A sinistra la distribuzione dei rendimenti giornalieri di Bitcoin (2017-2026) "
    "con sovrapposta la curva a campana di pari media e deviazione: al centro il "
    "picco reale è molto più alto, e ai lati la realtà esce dal disegno. A destra i "
    "giorni estremi ogni mille sedute, per Bitcoin e per un'azione industriale "
    "quotata a Milano dal 2000, confrontati con quanti ne prevede la campana. La "
    "scala è logaritmica: le due barre di mercato stanno quasi sempre alla stessa "
    "altezza, mentre quella della campana precipita e oltre le otto deviazioni esce "
    "dal fondo del grafico. Le code grasse non sono una stranezza delle criptovalute: "
    "sono una proprietà dei mercati, e si vede meglio dove la volatilità è alta. Il "
    "peggior giorno di Bitcoin, a −39,5%, sta oltre undici deviazioni; quello di "
    "ENI, a −20,9%, oltre dodici."
)


def code(nome: str) -> dict:
    """Giorni oltre k deviazioni: quanti sono, e quanti ne prevede la campana."""
    r = rendimenti(carica(nome).sort("data")["chiusura"].to_numpy())
    mu, sigma = r.mean(), r.std(ddof=1)
    z = np.abs((r - mu) / sigma)
    return {
        "rendimenti": r,
        "n": len(r),
        "osservati": {k: int((z > k).sum()) for k in SOGLIE},
        "per_mille": {k: float((z > k).sum()) / len(r) * 1000 for k in SOGLIE},
        "previsti": {k: 2 * norm.sf(k) * len(r) for k in SOGLIE},
        "peggiore": float(r.min()),
        "sigma_peggiore": float(abs((r.min() - mu) / sigma)),
    }


def disegna(destinazione: str = "stampa"):
    dati = {nome: code(nome) for nome, _ in MERCATI}
    r = dati["btcusdt"]["rendimenti"]
    mu, sigma = r.mean(), r.std(ddof=1)

    fig, (sx, dx) = plt.subplots(1, 2, figsize=figsize("media"), width_ratios=[1.15, 1])

    bordi = np.linspace(-0.18, 0.18, 70)
    sx.hist(r, bins=bordi, density=True, facecolor="white", edgecolor="black", linewidth=0.6)
    x = np.linspace(-0.18, 0.18, 400)
    sx.plot(x, norm.pdf(x, mu, sigma), color="black", linestyle="--", linewidth=1.2)
    sx.annotate(t("la campana\nprevista", "the predicted\nbell curve"),
                xy=(0.075, 6), fontsize=6.5, linespacing=1.3)
    sx.set_xlabel(t("Rendimento giornaliero, Bitcoin", "Daily return, Bitcoin"))
    sx.set_ylabel(t("Densità", "Density"))
    sx.set_xticks([-0.15, 0, 0.15])
    sx.set_xticklabels(["−15%", "0", "+15%"])

    # Il tasso ogni mille sedute rende confrontabili una serie di nove anni e
    # una di ventisei. Il previsto dalla campana dipende solo dalla soglia.
    previsti = np.array([2 * norm.sf(k) * 1000 for k in SOGLIE])
    x2 = np.arange(len(SOGLIE))
    larghezza = 0.26
    stili = [
        ("#404040", "", "Bitcoin"),
        ("white", "///", "ENI"),
    ]
    for j, ((nome, etichetta), (colore, retino, _)) in enumerate(zip(MERCATI, stili)):
        valori = [dati[nome]["per_mille"][k] for k in SOGLIE]
        dx.bar(x2 + (j - 1) * larghezza, valori, width=larghezza, facecolor=colore,
               edgecolor="black", linewidth=0.75, hatch=retino, label=etichetta)
    dx.bar(x2 + larghezza, np.maximum(previsti, 3e-4), width=larghezza,
           facecolor="white", edgecolor="black", linewidth=0.75, hatch="...",
           label=t("campana", "bell curve"))

    dx.set_yscale("log")
    dx.set_xlim(-0.62, len(SOGLIE) - 0.28)
    dx.set_xticks(x2)
    dx.set_xticklabels([t(f"oltre {k}σ", f"beyond {k}σ") for k in SOGLIE], fontsize=6.5)
    dx.set_ylabel(t("Giorni ogni mille sedute\n(scala log.)", "Days per thousand sessions\n(log scale)"),
                  fontsize=7)
    dx.set_ylim(2e-4, 900)
    dx.grid(axis="x", visible=False)
    dx.legend(loc="upper right", fontsize=6.0, ncols=1)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte} (BTCUSDT) e Yahoo Finance (ENI.MI), chiusure giornaliere",
                  f"{fonte} (BTCUSDT) and Yahoo Finance (ENI.MI), daily closes"),
          estratto)

    disegna.numeri = {
        nome: {
            "n": d["n"],
            "osservati": d["osservati"],
            "previsti": d["previsti"],
            "peggiore": d["peggiore"],
            "sigma_peggiore": d["sigma_peggiore"],
        }
        for nome, d in dati.items()
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for nome, d in disegna.numeri.items():
        print(f"\n{nome}: {d['n']} rendimenti")
        for k in SOGLIE:
            print(f"  oltre {k}σ: osservati {d['osservati'][k]:4d}"
                  f"  previsti {num(d['previsti'][k], 3)}")
        print(f"  peggior giorno {d['peggiore']:+.1%} = {d['sigma_peggiore']:.1f} σ")
