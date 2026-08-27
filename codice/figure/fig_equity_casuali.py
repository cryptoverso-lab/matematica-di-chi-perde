"""Cap. 4 — Dodici curve di capitale generate dal puro caso.

Nessuna abilita', nessun segnale, nessuna strategia: solo numeri casuali con
media zero. Il compito del lettore e' indovinare quale sia "brava".
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook import seed_for  # noqa: E402
from cvbook.layout import figsize  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.simulazioni import equity_casuali  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-04"
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Dodici curve di capitale su due anni di operatività simulata. Nessuna di "
    "esse contiene la minima abilità: sono numeri casuali con vantaggio "
    "atteso esattamente zero. Alcune salgono con una regolarità che, se te la "
    "mostrassero come risultato di un metodo, troveresti convincente. Il caso "
    "non produce solo rumore: produce anche storie che sembrano avere un "
    "senso."
)


def disegna(destinazione: str = "stampa"):
    rng = np.random.default_rng(seed_for("equity-casuali-griglia"))
    curve = equity_casuali(12, 500, volatilita_periodo=0.018, rng=rng)

    fig, assi = plt.subplots(3, 4, figsize=figsize("alta"), sharex=True, sharey=True)

    for k, (ax, curva) in enumerate(zip(assi.flat, curve)):
        ax.plot(curva * 100, color="black", linewidth=0.85)
        ax.axhline(100, color="#8C8C8C", linestyle=":", linewidth=0.7)
        ax.set_title(chr(ord("A") + k), fontsize=6.5, pad=1.5)
        ax.tick_params(labelsize=5.5, length=2)
        ax.grid(visible=False)
        for lato in ("top", "right"):
            ax.spines[lato].set_visible(False)

    assi[1, 0].set_ylabel(t("Capitale (100 = iniziale)", "Capital (100 = starting)"), fontsize=6.5)
    assi[2, 0].set_xlabel(t("Giorni", "Days"), fontsize=6.5)

    firma(fig, t("simulazione, seme fisso, vantaggio atteso nullo",
                  "simulation, fixed seed, zero expected edge"), "—")
    return fig
