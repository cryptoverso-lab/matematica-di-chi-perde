"""Cap. 23 — Cosa succede quando puoi provare mille idee in un pomeriggio.

Piu' tentativi si fanno, piu' strategie "funzionanti" si trovano: cresce senza
limite, perche' e' un effetto del cercare, non del trovare. La quota che
sopravvive fuori campione, invece, resta inchiodata al livello del caso.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook import seed_for  # noqa: E402
from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t as tr  # noqa: E402
from cvbook.metriche import rendimenti  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-23"
TENTATIVI = [10, 50, 100, 500, 1000, 2000]
DIDASCALIA = (
    "Regole generate a caso e valutate sulla prima metà della storia: si tiene "
    "quelle che superano il capitale iniziale. La linea continua conta quante "
    "\"funzionano\" — e cresce indefinitamente con il numero di tentativi, perché "
    "trovarle è una conseguenza del cercare. La linea tratteggiata conta quante di "
    "quelle continuano a funzionare sulla seconda metà, mai vista: resta attorno al "
    "livello che ci si aspetta dal puro caso. Poter provare mille idee in un "
    "pomeriggio non accelera la scoperta: accelera la produzione di illusioni."
)


def disegna(destinazione: str = "stampa"):
    r = rendimenti(carica("btcusdt")["chiusura"].to_numpy())
    meta = len(r) // 2
    rng = np.random.default_rng(seed_for("velocita-illusione"))

    massimo = max(TENTATIVI)
    dentro = np.empty(massimo)
    fuori = np.empty(massimo)

    for k in range(massimo):
        # Una "idea" è una regola di esposizione generata a caso: nessuna
        # informazione, ma nemmeno meno sensata di molte regole vere.
        soglia = rng.uniform(-0.6, 0.6)
        rumore = rng.normal(size=len(r))
        segnale = (rumore > soglia).astype(float)
        dentro[k] = np.prod(1 + segnale[:meta] * r[:meta])
        fuori[k] = np.prod(1 + segnale[meta:] * r[meta:])

    trovate, sopravvissute = [], []
    for n in TENTATIVI:
        ok = dentro[:n] > 1.0
        trovate.append(int(ok.sum()))
        sopravvissute.append(int((ok & (fuori[:n] > 1.0)).sum()))

    fig, ax = plt.subplots()
    ax.plot(TENTATIVI, trovate, color="black", linestyle="-", linewidth=1.3,
            marker="o", markersize=3)
    ax.plot(TENTATIVI, sopravvissute, color="#8C8C8C", linestyle="--", linewidth=1.3,
            marker="s", markersize=3)

    ax.text(0.04, 0.94, tr("«funzionano» sui dati usati per cercarle",
                           "“work” on the data used to search for them"),
            transform=ax.transAxes, fontsize=7, va="top")
    ax.text(0.04, 0.87, tr("funzionano anche sui dati mai visti", "also work on data never seen"),
            transform=ax.transAxes, fontsize=7, color="#595959", va="top")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(tr("Idee provate", "Ideas tried"))
    ax.set_ylabel(tr("Idee che «funzionano» (scala log.)", "Ideas that “work” (log scale)"))
    ax.set_xticks(TENTATIVI)
    # Migliaia col punto: «1000» in un libro italiano si legge male accanto
    # ai numeri all'italiana del resto della figura.
    ax.set_xticklabels([f"{v:,}".replace(",", ".") for v in TENTATIVI])
    ax.grid(which="minor", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, tr(f"{fonte}, BTCUSDT — regole generate casualmente",
                   f"{fonte}, BTCUSDT — randomly generated rules"), estratto)
    return fig
