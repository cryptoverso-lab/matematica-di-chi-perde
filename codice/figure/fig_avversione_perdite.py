"""Cap. 6 — La funzione del valore percepito.

Il dolore di una perdita non e' il rovescio del piacere di un guadagno della
stessa misura: e' circa il doppio. La forma di questa curva e' il risultato
sperimentale piu' replicato dell'economia comportamentale, e spiega da sola
meta' degli errori operativi.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma, num, tacca  # noqa: E402

CAPITOLO = "sec-cap-06"
ALFA = 0.88   # curvatura, dai lavori sperimentali originali
LAMBDA = 2.25  # quanto pesa di piu' una perdita rispetto a un guadagno pari
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Valore soggettivo attribuito a un guadagno e a una perdita della stessa "
    "entità, secondo i parametri stimati sperimentalmente dalla teoria del "
    "prospetto. L'unità dell'asse verticale è il piacere di guadagnare 3.000 "
    "euro: perderne 3.000 vale −2,25, cioè il dispiacere è 2,25 volte più "
    "grande. La curva è anche più piatta verso l'esterno, e la punteggiata "
    "dice quanto: è il dolore che si proverebbe se crescesse sempre al ritmo "
    "iniziale. La differenza fra perdere 8.000 e perderne 10.000 si sente "
    "molto meno di quella fra perdere zero e perderne 2.000."
)


def disegna(destinazione: str = "stampa"):
    x = np.linspace(-10, 10, 400)
    # np.where valuta entrambi i rami: si eleva il valore assoluto e si rimette
    # il segno dopo, per non calcolare la potenza frazionaria di un negativo.
    grandezza = np.abs(x) ** ALFA
    v = np.where(x >= 0, grandezza, -LAMBDA * grandezza)

    # L'asse verticale era senza tacche: la didascalia dichiarava «2,25 volte»
    # e il lettore non aveva modo di leggerlo dal grafico. Si normalizza sul
    # valore del guadagno di riferimento, cosi' l'unita' e' «quanto vale il
    # piacere di guadagnare 3.000 euro» e le due tacche dicono +1 e -2,25.
    g = 3.0
    unita = g**ALFA
    v = v / unita

    fig, ax = plt.subplots()
    ax.plot(x, v, color="black", linewidth=1.3)
    ax.axhline(0, color="black", linewidth=0.75)
    ax.axvline(0, color="black", linewidth=0.75)

    # La pendenza del ramo delle perdite vicino all'origine, prolungata: lo
    # scostamento fra la curva e questa retta E' l'appiattimento di cui parla
    # la didascalia, che altrimenti non si vede a occhio.
    pendenza = (v[np.argmin(np.abs(x + 0.5))]) / (-0.5)
    sinistra = x[x <= 0]
    ax.plot(sinistra, pendenza * sinistra, linestyle=(0, (1, 2)),
            color="#8C8C8C", linewidth=0.8)
    ax.annotate(
        t("se il dolore crescesse\nsempre allo stesso ritmo",
          "if pain kept growing\nat the same rate"),
        xy=(-6.2, pendenza * -6.2),
        xytext=(8, -8),
        textcoords="offset points",
        fontsize=6.5,
        linespacing=1.3,
        color="#595959",
        ha="left",
        va="top",
    )

    vg = 1.0
    vp = -LAMBDA
    for valore, testo, va in (
        (vg, t(f"guadagno {g:.0f}", f"gain {g:.0f}"), "bottom"),
        (vp, t(f"perdita {g:.0f}", f"loss {g:.0f}"), "top"),
    ):
        segno = 1 if valore > 0 else -1
        ax.plot([segno * g, segno * g], [0, valore], linestyle=":", color="#595959", linewidth=0.9)
        ax.plot([0, segno * g], [valore, valore], linestyle=":", color="#595959", linewidth=0.9)
        ax.annotate(testo, xy=(segno * g, valore), xytext=(6 * segno, 0),
                    textcoords="offset points", fontsize=7,
                    ha="left" if segno > 0 else "right", va="center")

    # Il riquadro bianco di questa etichetta CANCELLAVA un tratto della curva,
    # e proprio quello che la didascalia manda a guardare: il ramo delle perdite
    # spariva verso -6,5 e ricompariva come moncone staccato. Il testo va dove
    # non c'e' nulla da coprire — il quadrante in alto a sinistra e' vuoto — e
    # senza riquadro opaco.
    ax.text(
        -9.6, 1.9,
        t("il dolore è circa\n2,25 volte il piacere",
          "the pain is about\n2.25 times the pleasure"),
        fontsize=7,
        linespacing=1.35,
        ha="left",
        va="center",
    )

    ax.set_xlabel(t("Esito monetario (migliaia di euro)", "Monetary outcome (thousands of euros)"))
    ax.set_ylabel(t("Valore percepito\n(1 = piacere di guadagnare 3.000)",
                    "Perceived value\n(1 = pleasure of gaining 3,000)"))
    ax.set_yticks([vp, -1, 0, vg])
    ax.set_yticklabels([tacca(vp), tacca(-1), tacca(0), num(1, 0, segno=True)])
    ax.grid(visible=False)
    for lato in ("top", "right", "bottom", "left"):
        ax.spines[lato].set_visible(False)

    firma(fig, t("parametri sperimentali della teoria del prospetto",
                  "experimental parameters from prospect theory"), "—")
    return fig
