"""Cap. prezzo e tempo — Il volume non e' una terza dimensione: e' il calendario.

I derivati non scadono quando capita. Sull'IDEM di Borsa Italiana indici e azioni
scadono il **terzo venerdi'** del mese; sui future e sulle opzioni in criptovaluta
la scadenza mensile e' l'**ultimo venerdi'**. Sono date pubbliche, note con anni
di anticipo, che non dicono niente su dove andra' il prezzo. Il volume, pero', le
sente: la figura misura di quanto.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.ciclica import effetto_scadenza  # noqa: E402
from cvbook.dati import carica  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-ciclica"

SERIE = [
    ("generali", "Generali", False),
    ("enel", "Enel", False),
    ("eni", "ENI", False),
    ("intesa", "Intesa Sanpaolo", False),
    ("ftsemib", "FTSE MIB", False),
    ("btcusdt", "Bitcoin", True),
    ("ethusdt", "Ethereum", True),
    ("solusdt", "Solana", True),
]

#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Quanto volume in più si scambia nel giorno in cui scadono i derivati. "
    "Sulle quattro azioni italiane e sull'indice la scadenza è il terzo "
    "venerdì del mese, sulle criptovalute l'ultimo: date di calendario, "
    "pubbliche, note con anni di anticipo, che non contengono nessuna "
    "informazione su dove andrà il prezzo. La barra chiara confronta con un "
    "giorno qualunque; quella scura, che è quella che conta, con un altro "
    "venerdì dello stesso mercato — perché la scadenza cade sempre di "
    "venerdì, e il venerdì non è un giorno qualunque. Sulle azioni italiane "
    "il confronto onesto non toglie quasi niente. Sulle criptovalute porta "
    "via tutto: lì non era la scadenza, era il venerdì."
)


def _misure() -> list[dict]:
    fuori = []
    for nome, etichetta, cripto in SERIE:
        df = carica(nome).sort("data")
        e = effetto_scadenza(df["data"].to_list(), df["volume"].to_numpy(),
                             cripto=cripto)
        fuori.append({"etichetta": etichetta, "cripto": cripto, **e})
    return fuori


def disegna(destinazione: str = "stampa"):
    righe = _misure()
    y = np.arange(len(righe))
    grezzo = np.array([r["eccesso_grezzo"] for r in righe])
    netto = np.array([r["eccesso"] for r in righe])

    scuro, chiaro = "#333333", "#FFFFFF"
    if destinazione == "schermo":
        from cvbook.stile import BRAND
        scuro = BRAND["blu"]

    fig, ax = plt.subplots(figsize=(4.25, 4.25 * 0.72))
    alto = 0.36
    ax.barh(y + alto / 2 + 0.02, grezzo, height=alto, facecolor=chiaro,
            edgecolor="black", linewidth=0.75, hatch="///",
            label=t("contro un giorno qualunque", "vs. an ordinary day"))
    ax.barh(y - alto / 2 - 0.02, netto, height=alto, facecolor=scuro,
            edgecolor="black", linewidth=0.75,
            label=t("contro un altro venerdì", "vs. another Friday"))

    for yi, g, n in zip(y, grezzo, netto):
        ax.annotate(num(g, 0, segno=True, percento=True),
                    xy=(max(g, 0), yi + alto / 2 + 0.02), xytext=(4, 0),
                    textcoords="offset points", fontsize=6.5, va="center", ha="left")
        ax.annotate(num(n, 0, segno=True, percento=True),
                    xy=(max(n, 0), yi - alto / 2 - 0.02), xytext=(4, 0),
                    textcoords="offset points", fontsize=6.5, va="center", ha="left")

    ax.set_yticks(y, [r["etichetta"] for r in righe])
    ax.set_xlim(0, max(grezzo.max(), netto.max()) * 1.20)
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, pos=None: num(x, 0, percento=True))
    )
    ax.set_xlabel(t("Volume in più nel giorno di scadenza", "Extra volume on expiry day"))
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, frameon=False)

    # Le due famiglie hanno due calendari diversi: dirlo sulla figura, non solo
    # nella didascalia, perche' la figura viaggia da sola.
    # The two families have two different calendars: state it on the figure
    # itself, not only in the caption, because the figure travels on its own.
    ax.annotate(
        t("scadenza: terzo venerdì per le italiane,\nultimo venerdì per le criptovalute",
          "expiry: third Friday for Italian stocks,\nlast Friday for cryptocurrencies"),
        xy=(0.98, 0.98), xycoords="axes fraction", fontsize=6.5,
        ha="right", va="top", linespacing=1.35)

    firma(fig, t("Binance Data Vision e Yahoo Finance, volumi giornalieri",
                  "Binance Data Vision and Yahoo Finance, daily volumes"), "")

    italiane = [r for r in righe if not r["cripto"]]
    cripto = [r for r in righe if r["cripto"]]
    azioni = [r for r in italiane if r["etichetta"] != "FTSE MIB"]
    disegna.numeri = {
        "azioni_min": min(r["eccesso"] for r in azioni),
        "azioni_max": max(r["eccesso"] for r in azioni),
        "ftsemib": next(r["eccesso"] for r in italiane if r["etichetta"] == "FTSE MIB"),
        "cripto_min": min(r["eccesso"] for r in cripto),
        "cripto_max": max(r["eccesso"] for r in cripto),
        "cripto_grezzo_max": max(r["eccesso_grezzo"] for r in cripto),
        "scadenze_generali": next(r["scadenze"] for r in righe
                                  if r["etichetta"] == "Generali"),
        **{f"eccesso_{r['etichetta'].split()[0].lower()}": r["eccesso"] for r in righe},
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:22s} {v}")
