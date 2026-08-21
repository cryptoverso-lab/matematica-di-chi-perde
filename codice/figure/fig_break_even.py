"""Cap. 3 — Il rendimento lordo che serve per finire in pari.

Non "quanto guadagno": quanto devo azzeccare prima ancora di cominciare a
guadagnare. E' il numero che nessuna pubblicita' mostra.

La soglia di confronto non e' piu' un rendimento medio citato a memoria: e'
il rendimento composto annuo di una blue chip italiana sui dati congelati di
questo libro, ventisei anni e mezzo, dividendi inclusi. Un libro che chiede a
tutti di poter rieseguire non puo' tracciare una riga di riferimento che non
viene da nessuna parte.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-03"
RIFERIMENTO = "eni"
DIDASCALIA = (
    "Rendimento lordo annuo necessario soltanto per chiudere l'anno in pari, in "
    "funzione di quante operazioni complete si fanno e di quanto costa ciascuna. "
    "A una operazione al giorno con costi da piccolo operatore servono oltre "
    "ottanta punti percentuali l'anno prima di guadagnare il primo euro. La riga "
    "orizzontale non è un rendimento citato a memoria: è quello che una blue chip "
    "italiana ha effettivamente prodotto, composto e con i dividendi reinvestiti, "
    "nei ventisei anni e mezzo dei dati di questo libro. Tutto ciò che sta sopra "
    "quella riga è territorio in cui il solo costo si mangia più di quanto un "
    "titolo intero abbia reso in un quarto di secolo."
)


def riferimento_annuo() -> float:
    """Rendimento composto annuo della serie di riferimento, sui dati congelati."""
    df = carica(RIFERIMENTO).sort("data")
    prezzi = df["chiusura"].to_numpy()
    date = df["data"].to_list()
    anni = (date[-1] - date[0]).days / 365.25
    return float((prezzi[-1] / prezzi[0]) ** (1 / anni) - 1)


def disegna(destinazione: str = "stampa"):
    operazioni = np.array([1, 4, 12, 26, 52, 104, 250])
    costi = [(0.0006, t("0,06% a giro", "0.06% per round trip"), "-", "#000000"),
             (0.0012, t("0,12% a giro", "0.12% per round trip"), "--", "#595959"),
             (0.0025, t("0,25% a giro", "0.25% per round trip"), "-.", "#8C8C8C")]

    soglia = riferimento_annuo() * 100

    fig, ax = plt.subplots()

    for costo, etichetta, tratto, grigio in costi:
        # Serve un lordo tale che (1+lordo)*(1-costo)^n = 1
        necessario = ((1 - costo) ** (-operazioni) - 1) * 100
        ax.plot(operazioni, necessario, linestyle=tratto, color=grigio,
                linewidth=1.2, marker="o", markersize=2.4)
        ax.annotate(
            etichetta,
            xy=(operazioni[-1], min(necessario[-1], 97)),
            xytext=(-3, 4),
            textcoords="offset points",
            fontsize=6.5,
            ha="right",
        )

    ax.axhline(soglia, color="black", linewidth=0.75, linestyle=":")
    ax.annotate(
        t(
            f"{num(soglia, 1)}% l'anno: quanto ha reso una blue chip\n"
            "italiana dal 2000, dividendi inclusi",
            f"{num(soglia, 1)}% a year: what an Italian blue chip\n"
            "returned since 2000, dividends included",
        ),
        xy=(1.3, soglia + 3),
        fontsize=6.5,
        linespacing=1.3,
    )

    ax.set_xscale("log")
    ax.set_xlabel(t("Operazioni complete all'anno", "Round trips per year"))
    ax.set_ylabel(t("Rendimento lordo per andare in pari (%)", "Gross return to break even (%)"))
    ax.set_xticks([1, 4, 12, 52, 250])
    ax.set_xticklabels(["1", "4", "12", "52", "250"])
    ax.set_ylim(0, 100)
    ax.grid(which="minor", visible=False)

    fonte, estratto = citazione(RIFERIMENTO)
    firma(fig, t(
        f"calcolo diretto; la soglia di confronto da {fonte}, ENI.MI 2000-2026",
        f"direct calculation; comparison threshold from {fonte}, ENI.MI 2000-2026",
    ), estratto)

    disegna.numeri = {
        "soglia": soglia,
        "pareggio": {
            int(n): float(((1 - c) ** (-n) - 1) * 100)
            for c in (0.0006, 0.0012, 0.0025)
            for n in operazioni
            if c == 0.0012 or n in (52, 250)
        },
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    print(f"soglia di riferimento: {disegna.numeri['soglia']:.2f}% annuo")
    for costo in (0.0006, 0.0012, 0.0025):
        righe = ", ".join(
            f"{n}op {((1 - costo) ** (-n) - 1) * 100:.2f}%"
            for n in (1, 4, 12, 26, 52, 104, 250)
        )
        print(f"  costo {costo:.4f}: {righe}")
