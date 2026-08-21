"""Cap. 1 — Quanto pesa il tempo, e perche' questa figura va guardata con sospetto.

Mostra la quota di ingressi che finisce in perdita al crescere dell'orizzonte.
E' anche il primo esempio, dichiarato, di risultato che sembra piu' solido di
quanto sia: il campione copre un solo asset in un solo periodo, per giunta
fortunato. Il capitolo lo smonta invece di nasconderlo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-01"
ORIZZONTI = [
    (30, t("1 mese", "1 month")), (90, t("3 mesi", "3 months")), (365, t("1 anno", "1 year")),
    (730, t("2 anni", "2 years")), (1460, t("4 anni", "4 years")),
]
DIDASCALIA = (
    "Quota di giorni d'ingresso che, dopo il periodo indicato, si trova in perdita. "
    "Piu' l'orizzonte si allunga, meno conta il momento in cui si è cominciato. "
    "Attenzione però: il campione è un solo asset in un solo periodo, e per giunta "
    "un periodo in cui quell'asset è cresciuto moltissimo. La colonna dei quattro anni "
    "non dice che a quattro anni non si perde: dice che qui, in questa finestra, non è "
    "successo. E' esattamente il tipo di conclusione che questo libro insegna a rifiutare."
)


def disegna(destinazione: str = "stampa"):
    df = carica("btcusdt")
    p = df["chiusura"].to_numpy()

    etichette, quote, campioni = [], [], []
    for giorni, nome in ORIZZONTI:
        r = p[giorni:] / p[:-giorni] - 1.0
        etichette.append(nome)
        quote.append((r < 0).mean() * 100)
        campioni.append(len(r))

    fig, ax = plt.subplots()
    barre = ax.bar(
        etichette,
        quote,
        color="white",
        edgecolor="black",
        linewidth=0.75,
        hatch="///",
        width=0.62,
    )

    for barra, quota, n in zip(barre, quote, campioni):
        ax.annotate(
            f"{quota:.0f}%",
            xy=(barra.get_x() + barra.get_width() / 2, quota),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=7.5,
        )
        # La numerosita' del campione sta sotto l'asse, come una didascalia
        # della colonna: dentro la barra finiva sopra il retino.
        ax.annotate(
            # Migliaia col punto: il separatore inglese in un libro italiano
            # si legge come una virgola decimale.
            f"n = {n:,}".replace(",", "."),
            xy=(barra.get_x() + barra.get_width() / 2, 0),
            xytext=(0, -22),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=6,
            color="#595959",
            annotation_clip=False,
        )

    ax.set_ylabel(t("Ingressi in perdita (%)", "Entries at a loss (%)"))
    # Spazio sotto le tacche per la riga delle numerosita'.
    ax.set_xlabel(t("Tempo trascorso dall'ingresso", "Time elapsed since entry"), labelpad=18)
    ax.set_ylim(0, 55)
    ax.grid(axis="x", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTCUSDT giornaliero 2017-2026", f"{fonte}, daily BTCUSDT 2017-2026"), estratto)
    return fig
