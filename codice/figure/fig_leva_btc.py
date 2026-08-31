"""Cap. 2 — La leva: avere ragione e perdere lo stesso.

Dal 1 gennaio 2021 Bitcoin raddoppia. Chi ha usato leva giornaliera 2x sullo
stesso periodo e nella stessa direzione perde piu' di un terzo del capitale;
con leva 3x ne perde il 97%. Non e' un errore di previsione: e' aritmetica.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.layout import figsize  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.metriche import rendimenti  # noqa: E402
from cvbook.stile import firma, num, tacca  # noqa: E402

CAPITOLO = "sec-cap-02"
INIZIO = "2021-01-01"
LEVE = [(1, "-", "#000000"), (2, "--", "#595959"), (3, "-.", "#8C8C8C")]
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Capitale nel tempo con leva giornaliera ribilanciata, dal 1° gennaio "
    "2021. L'asset sottostante raddoppia; chi lo ha seguito con leva 2× "
    "chiude a 0,63 volte il capitale iniziale, con leva 3× a 0,03. La "
    "direzione era giusta per tutti e tre. Sulla scala logaritmica ogni tacca "
    "vale un fattore dieci: la distanza fra le curve è molto più grande di "
    "quanto l'occhio suggerisca."
)


def disegna(destinazione: str = "stampa"):
    df = carica("btcusdt")
    prezzi = df["chiusura"].to_numpy()
    date = df["data"].to_list()

    i = date.index(dt.date.fromisoformat(INIZIO))
    r = rendimenti(prezzi)[i:]
    x = np.arange(len(r) + 1) / 365.0

    fig, ax = plt.subplots(figsize=figsize("alta"))

    # Etichette in posizioni fisse: agganciate alla curva si sovrappongono al tratto.
    posizioni = {1: (2.35, 2.9), 2: (2.35, 0.30), 3: (2.35, 0.033)}

    for leva, tratto, grigio in LEVE:
        curva = np.concatenate([[1.0], np.cumprod(1 + leva * r)])
        ax.plot(x, curva, linestyle=tratto, color=grigio, linewidth=1.2)
        finale = f"{num(curva[-1], 2)}"
        px, py = posizioni[leva]
        # L'etichetta prende il colore della propria curva: nere tutte e tre,
        # non si capiva quale riga descrivesse quale tracciato. Il grigio piu'
        # chiaro resta per il tratto e sale a #595959 per il testo, che a 7 pt
        # sotto quel livello non regge la stampa.
        ax.annotate(
            t(f"leva {leva}× → {finale}×", f"leverage {leva}× → {finale}×"),
            xy=(px, py),
            fontsize=7,
            ha="left",
            va="center",
            color="#595959" if grigio == "#8C8C8C" else grigio,
            bbox=dict(boxstyle="square,pad=0.12", facecolor="white", edgecolor="none"),
        )

    ax.axhline(1.0, color="black", linewidth=0.75, linestyle=":")
    ax.set_yscale("log")
    ax.set_ylim(0.003, 6)
    ax.set_yticks([0.01, 0.1, 1, 5])
    ax.set_yticklabels([tacca(v, "×") for v in (0.01, 0.1, 1, 5)])
    ax.set_xlabel(t("Anni dall'inizio", "Years from start"))
    ax.set_ylabel(t("Capitale (scala logaritmica)", "Capital (log scale)"))

    ax.annotate(
        t("qui sotto il capitale\nè praticamente perduto", "below here the capital\nis practically lost"),
        xy=(0.15, 0.0055),
        fontsize=6.5,
        color="#595959",
        linespacing=1.3,
    )

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT giornaliero", f"{fonte}, daily BTCUSDT"), estratto)
    return fig
