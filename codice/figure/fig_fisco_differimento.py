"""Cap. fisco — Non e' l'aliquota: e' il momento in cui paghi.

Stesso rendimento lordo, stessa aliquota, due sole differenze: uno paga
l'imposta ogni anno sul realizzato, l'altro la paga tutta alla fine. Il
secondo finisce con molti piu' soldi, perche' nel frattempo ha continuato a
comporre anche la parte che il primo aveva gia' versato.

L'aliquota usata e' un parametro dichiarato, non una verita' di legge: le
aliquote cambiano, il meccanismo no.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.lingua import t as tr  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-fisco"
ALIQUOTA = 0.26
ORIZZONTI = np.arange(1, 31)
RENDIMENTI = [0.05, 0.10, 0.20]
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "A sinistra: mille euro fatti crescere al 10% lordo annuo per trent'anni, "
    "con la stessa aliquota del 26% applicata in due momenti diversi. Chi "
    "realizza e paga ogni anno finisce con 8.514 euro; chi lascia correre e "
    "paga tutto alla fine ne ha 13.173. La differenza — il 55% in più — non "
    "viene da un rendimento migliore: è l'imposta versata presto che smette "
    "di lavorare. A destra: quanto vale quel differimento al crescere "
    "dell'orizzonte e del rendimento. È il costo silenzioso di operare "
    "spesso, e non compare in nessun backtest."
)


def _confronto(rendimento: float, anni: int, aliquota: float = ALIQUOTA):
    """(capitale con imposta annuale, capitale con imposta differita)."""
    annuale = (1 + rendimento * (1 - aliquota)) ** anni
    lordo = (1 + rendimento) ** anni
    differita = 1 + (lordo - 1) * (1 - aliquota)
    return annuale, differita


def disegna(destinazione: str = "stampa"):
    fig, (sx, dx) = plt.subplots(1, 2, figsize=(4.25, 4.25 * 0.62))

    anni = np.arange(0, 31)
    annuale = np.array([_confronto(0.10, a)[0] for a in anni]) * 1000
    differita = np.array([_confronto(0.10, a)[1] for a in anni]) * 1000

    sx.plot(anni, differita, color="black", linewidth=1.2)
    sx.plot(anni, annuale, color="#595959", linewidth=1.2, linestyle="--")
    sx.fill_between(anni, annuale, differita, facecolor="white", edgecolor="#8C8C8C",
                    hatch="...", linewidth=0.0)
    sx.annotate(tr("imposta alla fine", "tax at the end"), xy=(30, differita[-1]), xytext=(-2, 3),
                textcoords="offset points", fontsize=6.5, ha="right")
    sx.annotate(tr("imposta ogni anno", "tax every year"), xy=(30, annuale[-1]), xytext=(-2, -12),
                textcoords="offset points", fontsize=6.5, ha="right", va="top",
                bbox=dict(boxstyle="square,pad=0.15", facecolor="white",
                          edgecolor="none"))
    sx.set_xlabel(tr("Anni", "Years"))
    sx.set_ylabel(tr("Capitale netto (euro, da 1.000)", "Net capital (euros, starting from 1,000)"))
    sx.set_xlim(0, 30)

    tratti = ["-.", "--", "-"]
    grigi = ["#8C8C8C", "#595959", "#000000"]
    for r, tratto, g in zip(RENDIMENTI, tratti, grigi):
        divario = np.array([
            (_confronto(r, a)[1] / _confronto(r, a)[0] - 1) * 100 for a in ORIZZONTI
        ])
        dx.plot(ORIZZONTI, divario, linestyle=tratto, color=g, linewidth=1.1)
        dx.annotate(tr(f"{r:.0%} lordo", f"{r:.0%} gross"), xy=(ORIZZONTI[-1], divario[-1]),
                    xytext=(-2, 2), textcoords="offset points", fontsize=6.5, ha="right")
    dx.set_xlabel(tr("Orizzonte (anni)", "Horizon (years)"))
    dx.set_ylabel(tr("Capitale in più differendo (%)", "Extra capital by deferring (%)"))
    dx.set_xlim(1, 30)

    firma(fig, tr(f"calcolo diretto, aliquota dichiarata {ALIQUOTA:.0%}",
                   f"direct calculation, stated tax rate {ALIQUOTA:.0%}"), "—")

    disegna.numeri = {
        "10pct_30anni_annuale": _confronto(0.10, 30)[0] * 1000,
        "10pct_30anni_differita": _confronto(0.10, 30)[1] * 1000,
        "divario_10pct_30anni": _confronto(0.10, 30)[1] / _confronto(0.10, 30)[0] - 1,
        "divario_10pct_10anni": _confronto(0.10, 10)[1] / _confronto(0.10, 10)[0] - 1,
        "divario_20pct_20anni": _confronto(0.20, 20)[1] / _confronto(0.20, 20)[0] - 1,
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:26s} {v:,.4f}")
