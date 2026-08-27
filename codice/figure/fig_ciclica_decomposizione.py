"""Cap. prezzo e tempo — Di tutto cio' che si spiega, quanto portano le due coordinate.

Bersaglio: l'ampiezza di un movimento concluso. Tre blocchi di spiegazione, tutti
misurati sulla stessa finestra e con lo stesso trattamento: quanto si muoveva il
prezzo in quei giorni, quanti giorni sono stati, quanto si scambiava in quei
giorni. La ripartizione e' quella di Shapley — la media su tutti gli ordini di
inserimento — perche' con variabili correlate «quanto spiega questa» dipende
dall'ordine, e la media su tutti gli ordini e' l'unica risposta senza arbitrio.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.ciclica import SOGLIA, decomposizione, tavolo  # noqa: E402
from cvbook.dati import carica  # noqa: E402
from cvbook.lingua import t as tr  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-ciclica"

#: Le otto serie con volume utilizzabile. Tre cripto e cinque italiane: se il
#: risultato reggesse solo sulle cripto sarebbe una curiosita' di un mercato.
SERIE = [
    ("btcusdt", "Bitcoin"),
    ("ethusdt", "Ethereum"),
    ("solusdt", "Solana"),
    ("ftsemib", "FTSE MIB"),
    ("eni", "ENI"),
    ("enel", "Enel"),
    ("intesa", "Intesa Sanpaolo"),
    ("generali", "Generali"),
]

#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Come si ripartisce ciò che tre colonne riescono a spiegare dell'ampiezza "
    "di un movimento: quanto veloce andava il prezzo, quanti giorni è durato, "
    "quanto volume si scambiava. Le barre sono normalizzate a cento: dicono "
    "le quote, non il totale, che è stampato a destra insieme a quanti "
    "movimenti lo producono. Il tempo pesa più della velocità su tutte e otto "
    "le serie. Il volume — stessa finestra, stesso trattamento, nessun "
    "handicap — sta sotto un decimo su sei serie su otto, e non arriva a un "
    "quinto nemmeno sulla peggiore."
)


def _quote() -> list[dict]:
    fuori = []
    for nome, etichetta in SERIE:
        df = carica(nome).sort("data")
        t = tavolo(df["chiusura"].to_numpy(), df["volume"].to_numpy(), SOGLIA)
        d = decomposizione(t)
        totale = d["velocita"] + d["tempo"] + d["volume"]
        fuori.append({
            "etichetta": etichetta,
            "velocita": d["velocita"] / totale,
            "tempo": d["tempo"] / totale,
            "volume": d["volume"] / totale,
            "spiegato": d["totale"],
            "movimenti": int(d["movimenti"]),
            "quota": d["quota_velocita_e_tempo"],
        })
    return fuori


def disegna(destinazione: str = "stampa"):
    righe = _quote()
    # Dall'alto in basso nell'ordine dichiarato: la lettura segue l'elenco.
    y = np.arange(len(righe))[::-1]

    grigi = ["#333333", "#BFBFBF", "#FFFFFF"]
    retini = ["", "", "///"]
    if destinazione == "schermo":
        from cvbook.stile import BRAND
        grigi = [BRAND["blu"], "#9FB0DE", "#FFFFFF"]

    fig, ax = plt.subplots(figsize=(4.25, 4.25 * 0.80))

    ETICHETTE_COLONNA = {
        "velocita": tr("velocità", "speed"),
        "tempo": tr("tempo", "time"),
        "volume": tr("volume", "volume"),
    }

    sinistra = np.zeros(len(righe))
    for chiave, colore, retino in zip(("velocita", "tempo", "volume"), grigi, retini):
        valori = np.array([r[chiave] for r in righe])
        ax.barh(y, valori, left=sinistra, height=0.62, facecolor=colore,
                edgecolor="black", linewidth=0.75, hatch=retino,
                label=ETICHETTE_COLONNA[chiave])
        for yi, v, s in zip(y, valori, sinistra):
            if v > 0.11:
                # Sul segmento del volume la riga tratteggiata del 90% passa
                # sopra la cifra: li' serve un riquadro bianco, che sul retino
                # bianco non si vede. Sugli altri due il riquadro si vedrebbe.
                ax.annotate(num(v, 0, percento=True), xy=(s + v / 2, yi),
                            ha="center", va="center", fontsize=6.5,
                            color="white" if chiave == "velocita" else "black",
                            bbox=dict(boxstyle="square,pad=0.12",
                                      facecolor="white", edgecolor="none")
                            if chiave == "volume" else None)
        sinistra = sinistra + valori

    ax.axvline(0.90, color="black", linewidth=0.75, linestyle=":")
    ax.set_ylim(-0.95, len(righe) - 0.45)
    ax.annotate("90%", xy=(0.90, -0.90), xytext=(-3, 0), textcoords="offset points",
                fontsize=6.5, ha="right", va="bottom")

    for r, yi in zip(righe, y):
        ax.annotate(
            tr(
                f"{r['movimenti']} movimenti\n{num(r['spiegato'], 0, percento=True)} spiegato",
                f"{r['movimenti']} movements\n{num(r['spiegato'], 0, percento=True)} explained",
            ),
            xy=(1.02, yi), fontsize=6.0, va="center", ha="left",
            color="#404040", linespacing=1.25)

    ax.set_yticks(y, [r["etichetta"] for r in righe])
    # La fascia oltre il 100% ospita le note: sta dentro gli assi, altrimenti
    # il layout automatico la taglierebbe.
    ax.set_xlim(0, 1.30)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0", "25%", "50%", "75%", "100%"])
    ax.set_xlabel(tr("Quota di ciò che le tre colonne spiegano insieme",
                      "Share of what the three columns explain together"))
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3, frameon=False)

    firma(fig, tr("Binance Data Vision e Yahoo Finance, chiusure giornaliere",
                   "Binance Data Vision and Yahoo Finance, daily closes"), "")

    # Due letture della stessa cosa, ed e' bene tenerle distinte.
    # `ripartizione`  = quota di Shapley di prezzo+tempo: attribuzione leale
    #                   delle tre colonne, e' cio' che disegnano le barre.
    # `quota`         = quanto il volume aggiunge a cio' che le altre due gia'
    #                   dicono, misurato come guadagno di R quadro.
    ripartizione = [r["velocita"] + r["tempo"] for r in righe]
    disegna.numeri = {
        "soglia": SOGLIA,
        "serie": len(righe),
        "ripartizione_minima": min(ripartizione),
        "ripartizione_massima": max(ripartizione),
        "serie_sopra_90": sum(1 for q in ripartizione if q >= 0.90),
        "quota_minima": min(r["quota"] for r in righe),
        "quota_massima": max(r["quota"] for r in righe),
        "tempo_batte_velocita": sum(1 for r in righe if r["tempo"] > r["velocita"]),
        **{f"ripartizione_{r['etichetta'].split()[0].lower()}": p + t
           for r, p, t in ((r, r["velocita"], r["tempo"]) for r in righe)},
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:22s} {v}")
