"""Cap. custodia — L'aritmetica di un rischio che nessuno dimensiona.

Due conti che si fanno a mente e che quasi nessuno fa. A sinistra: se un posto
in cui tieni i soldi ha una probabilita' annua di sparire, quella probabilita'
non resta piccola — si accumula sugli anni. A destra: quanto serve guadagnare
per rimettere a posto la perdita, in funzione di quanta parte del capitale
stava li' dentro.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.lingua import t as tr  # noqa: E402
from cvbook.metriche import recupero_necessario  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-custodia"
PROBABILITA = [0.01, 0.02, 0.05]
ANNI = np.arange(0, 21)
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "A sinistra: probabilità di subire almeno un evento di custodia nell'arco "
    "degli anni, per tre ipotesi di rischio annuo della singola sede. Anche "
    "l'ipotesi più prudente — un anno su cento — diventa quasi una "
    "probabilità su cinque su un orizzonte di vent'anni, ed è un orizzonte "
    "normale per chi investe. A destra: quanto bisogna guadagnare sul "
    "capitale rimasto per tornare al punto di partenza, in funzione della "
    "quota che stava nella sede fallita. La curva non è ripida: è verticale. "
    "Sopra il 50% smette di essere un problema di rendimento."
)


def disegna(destinazione: str = "stampa"):
    fig, (sx, dx) = plt.subplots(1, 2, figsize=(4.25, 4.25 * 0.62))

    tratti = ["-", "--", "-."]
    grigi = ["#000000", "#595959", "#8C8C8C"]
    for p, tratto, g in zip(PROBABILITA, tratti, grigi):
        cumulata = (1 - (1 - p) ** ANNI) * 100
        sx.plot(ANNI, cumulata, linestyle=tratto, color=g, linewidth=1.1)
        sx.annotate(tr(f"{p:.0%} l'anno", f"{p:.0%} a year"), xy=(ANNI[-1], cumulata[-1]),
                    xytext=(-2, 2), textcoords="offset points",
                    fontsize=6.5, ha="right")
    sx.set_xlabel(tr("Anni di permanenza", "Years held"))
    sx.set_ylabel(tr("Almeno un evento (%)", "At least one event (%)"))
    sx.set_xlim(0, 20)
    sx.set_ylim(0, 70)

    quote = np.linspace(0.02, 0.90, 200)
    recuperi = np.array([recupero_necessario(q) for q in quote]) * 100
    dx.plot(quote * 100, recuperi, color="black", linewidth=1.2)
    # Tutte e tre le etichette sopra e a sinistra del proprio punto: la curva
    # sale da sinistra verso destra, quindi a sinistra del punto lo spazio e'
    # sempre libero. Scritta a destra, quella del 25% finiva sul tracciato.
    # ...tranne quella del 25%, che a sinistra non ha piu' spazio: il suo punto
    # sta a un quarto dell'asse e l'etichetta, scritta verso sinistra, usciva
    # dal riquadro e finiva a cavallo della linea dell'asse. Quella va a
    # destra, dove sotto la curva il campo e' libero.
    # ...except the 25% one: its point sits a quarter along the axis and the
    # label, written leftwards, ran past the spine.
    for q in (0.25, 0.50, 0.75):
        r = recupero_necessario(q) * 100
        dx.plot([q * 100], [r], marker="o", markersize=3.2, color="black")
        a_destra = q == 0.25
        dx.annotate(f"{q:.0%} → +{r:.0f}%", xy=(q * 100, r),
                    xytext=(6 if a_destra else -6, 8), textcoords="offset points",
                    fontsize=6.5, ha="left" if a_destra else "right", va="bottom")
    dx.set_xlabel(tr("Quota del capitale nella sede (%)", "Share of capital at the venue (%)"))
    dx.set_ylabel(tr("Guadagno necessario per tornare in pari (%)", "Gain needed to break even (%)"))
    dx.set_ylim(0, 420)
    dx.text(0.03, 0.93, tr("al 100% la curva\nnon esiste più", "at 100% the curve\nno longer exists"),
            transform=dx.transAxes, fontsize=6.5, va="top", linespacing=1.3)

    firma(fig, tr("calcolo diretto, nessun dato di mercato", "direct calculation, no market data"), "—")

    disegna.numeri = {
        f"{p:.0%}/anno su 10 anni": 1 - (1 - p) ** 10 for p in PROBABILITA
    } | {
        f"{p:.0%}/anno su 20 anni": 1 - (1 - p) ** 20 for p in PROBABILITA
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:22s} {v:.1%}")
