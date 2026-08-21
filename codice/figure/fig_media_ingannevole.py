"""Cap. 2 — La media che non ottieni.

Due pannelli: a sinistra il caso da manuale (+50% e -50% alternati, media
aritmetica zero, capitale che si dissolve); a destra la stessa cosa misurata
sui dati reali di Bitcoin, dove il divario fra la media dichiarabile e quella
effettivamente ottenuta e' quasi la meta' del rendimento.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.layout import figsize  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.metriche import rendimenti  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-02"
DIDASCALIA = (
    "A sinistra: venti mosse alternate di +50% e -50%. La media aritmetica è "
    "esattamente zero, il capitale finale è il 5,6% di quello iniziale. A destra: "
    "la stessa forbice misurata su Bitcoin, 2017-2026. Il rendimento medio giornaliero "
    "è +0,144%, quello effettivamente composto +0,081%: la differenza, 0,062 punti, "
    "coincide con la metà della varianza giornaliera. Non è un caso né un errore di "
    "misura: è quanto la volatilità preleva dal risultato, sempre."
)


def disegna(destinazione: str = "stampa"):
    fig, (sx, dx) = plt.subplots(1, 2, figsize=figsize("media"))

    # --- Pannello sinistro: il caso da manuale
    alternati = np.array([0.5, -0.5] * 10)
    capitale = np.concatenate([[1.0], np.cumprod(1 + alternati)]) * 100
    sx.plot(capitale, color="black", linewidth=1.2, marker="o", markersize=2.2)
    sx.axhline(100, color="#8C8C8C", linestyle=":", linewidth=0.9)
    sx.annotate(
        t(f"resta il {num(capitale[-1], 1)}%", f"{num(capitale[-1], 1)}% remains"),
        xy=(len(capitale) - 1, capitale[-1]),
        xytext=(-4, 22),
        textcoords="offset points",
        fontsize=7,
        ha="right",
        arrowprops=dict(arrowstyle="->", linewidth=0.75, color="black"),
    )
    sx.set_title(t("+50% e −50% alternati", "+50% and −50% alternating"), fontsize=8)
    sx.set_xlabel(t("Mosse", "Moves"))
    sx.set_ylabel(t("Capitale (100 = iniziale)", "Capital (100 = starting)"))
    sx.set_ylim(0, 165)

    # --- Pannello destro: la stessa forbice sui dati reali
    r = rendimenti(carica("btcusdt")["chiusura"].to_numpy())
    aritmetica = r.mean() * 100
    geometrica = (np.prod(1 + r) ** (1 / len(r)) - 1) * 100
    drag = (r.std(ddof=1) ** 2) / 2 * 100

    barre = dx.bar(
        [t("dichiarata\n(media)", "stated\n(average)"), t("ottenuta\n(composta)", "obtained\n(compounded)")],
        [aritmetica, geometrica],
        color=["#404040", "white"],
        edgecolor="black",
        linewidth=0.75,
        width=0.5,
    )
    barre[1].set_hatch("///")

    for barra, valore in zip(barre, [aritmetica, geometrica]):
        dx.annotate(
            f"{num(valore, 3, segno=True)}%",
            xy=(barra.get_x() + barra.get_width() / 2, valore),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=7.5,
        )

    # A meta' altezza finiva addosso alla barra e all'etichetta di destra:
    # sta meglio in basso, dentro lo spazio libero fra le due barre.
    dx.annotate(
        t(f"la volatilità preleva\n{num(drag, 3)} punti al giorno",
          f"volatility takes away\n{num(drag, 3)} points a day"),
        xy=(0.99, 0.99),
        xycoords="axes fraction",
        fontsize=6.5,
        ha="right",
        va="top",
        linespacing=1.3,
    )
    dx.set_title(t("Bitcoin, rendimento giornaliero", "Bitcoin, daily return"), fontsize=8)
    dx.set_ylabel(t("Per giorno (%)", "Per day (%)"))
    dx.set_ylim(0, aritmetica * 1.35)
    dx.grid(axis="x", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT giornaliero 2017-2026", f"{fonte}, daily BTCUSDT 2017-2026"), estratto)
    return fig
