"""Cap. 3 — Quanto costa muoversi, su due mercati che non hanno nulla in comune.

Stessa identica posizione finale, stesso periodo, stesso asset: cambia solo
quante volte si entra e si esce. Il capitale che resta e' una funzione della
frequenza, e la funzione scende molto piu' in fretta di quanto sembri.

I due pannelli servono a togliere l'ultima scappatoia: l'erosione da costi non
e' un effetto della volatilita' delle cripto, e' aritmetica. La stessa curva
esce identica su una blue chip industriale quotata a Milano.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.layout import figsize  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.metriche import rendimenti  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-03"
COSTI = [
    (0.0006, "0,06%", "-", "#000000"),
    (0.0012, "0,12%", "--", "#595959"),
    (0.0025, "0,25%", "-.", "#8C8C8C"),
]

#: (snapshot, titolo del pannello, barre in un anno, ogni quante barre si rientra)
#: Le cripto non chiudono mai: l'anno sono 365 barre, la settimana 7, il mese 30.
#: La borsa italiana apre circa 252 giorni l'anno: la settimana e' 5 sedute, il
#: mese 21, il trimestre 63. Le due griglie dicono le stesse cose in due
#: calendari diversi, ed e' l'unico modo perche' «una volta al mese» significhi
#: la stessa cosa nei due pannelli.
MERCATI = [
    ("btcusdt", "Bitcoin, 2017-2026", 365, [1, 2, 3, 5, 7, 14, 30, 60, 90, 180, 365]),
    ("eni", "ENI, 2000-2026", 252, [1, 2, 3, 5, 10, 21, 42, 63, 126, 252]),
]

#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Capitale finale restando sempre investiti, ma rientrando in posizione "
    "ogni N giorni: la posizione è identica, cambia solo quante volte la si "
    "chiude e riapre. Le tre curve sono i tre costi tipici del mercato al "
    "dettaglio per un giro completo. A sinistra Bitcoin dal 2017, a destra "
    "un'azione industriale quotata a Milano dal 2000: volatilità, settore, "
    "valuta e durata sono diversi, la forma della curva è la stessa. Chi non "
    "ha mai operato porta a casa 13,7 volte il capitale su Bitcoin e 8,7 sul "
    "titolo; chi ha rifatto la stessa posizione ogni giorno con costi medi ne "
    "porta a casa 0,28 sul primo e due millesimi e mezzo sul secondo. I costi "
    "non erodono il rendimento: lo cancellano."
)


def _curve(nome: str, barre_anno: int, frequenze: list[int] | None = None):
    """Capitale finale al variare della frequenza, per ciascuno dei tre costi."""
    r = rendimenti(carica(nome).sort("data")["chiusura"].to_numpy())
    n = len(r)
    lordo = float(np.prod(1 + r))
    frequenze = np.array(frequenze if frequenze is not None else [barre_anno])
    per_anno = barre_anno / frequenze
    curve = {
        costo: np.array([lordo * (1 - costo) ** (n / f) for f in frequenze])
        for costo, _, _, _ in COSTI
    }
    return per_anno, curve, lordo


def disegna(destinazione: str = "stampa"):
    fig, assi = plt.subplots(1, 2, figsize=figsize("media"), sharey=True)

    numeri: dict[str, dict] = {}
    for ax, (nome, titolo, barre_anno, frequenze) in zip(assi, MERCATI):
        per_anno, curve, lordo = _curve(nome, barre_anno, frequenze)
        numeri[nome] = {"lordo": lordo, "per_anno": per_anno, "curve": curve}

        for costo, etichetta, tratto, grigio in COSTI:
            ax.plot(per_anno, curve[costo], linestyle=tratto, color=grigio,
                    linewidth=1.2, marker="o", markersize=2.0,
                    label=t(f"costo {etichetta}", f"cost {etichetta}"))

        ax.axhline(lordo, color="black", linewidth=0.75, linestyle=":")
        ax.annotate(t(f"mai: {num(lordo, 1)}×", f"never: {num(lordo, 1)}×"),
                    xy=(1.1, lordo), xytext=(0, 4),
                    textcoords="offset points", fontsize=6.5)

        ax.set_title(titolo, fontsize=7)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(t("Operazioni all'anno", "Round trips per year"))
        ax.set_xticks([1, 12, 52, barre_anno])
        ax.set_xticklabels(["1", "12", "52", str(barre_anno)])
        ax.set_xlim(0.8, barre_anno * 1.4)
        ax.grid(which="minor", visible=False)

    assi[0].set_ylabel(t("Capitale finale (× quello iniziale)", "Final capital (× starting capital)"))
    assi[0].set_ylim(4e-4, 60)
    assi[0].set_yticks([0.001, 0.01, 0.1, 1, 10])
    assi[0].set_yticklabels(["0,001×", "0,01×", "0,1×", "1×", "10×"])

    # Le tre etichette di costo stanno una volta sola, sul pannello di sinistra:
    # gli stili di tratto sono gli stessi a destra. In legenda e non sulle
    # curve, perche' nella zona in cui le curve si separano non c'e' spazio.
    assi[0].legend(loc="lower left", fontsize=6.0, borderpad=0.2)

    fonte_btc, estratto = citazione("btcusdt")
    fonte_eni, _ = citazione("eni")
    firma(fig, t(f"{fonte_btc} (BTCUSDT) e {fonte_eni} (ENI.MI), chiusure giornaliere",
                  f"{fonte_btc} (BTCUSDT) and {fonte_eni} (ENI.MI), daily closes"),
          estratto)

    disegna.numeri = numeri
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for nome, d in disegna.numeri.items():
        print(f"\n{nome}: senza mai operare {d['lordo']:.3f}×")
        for costo, etichetta, _, _ in COSTI:
            valori = ", ".join(
                f"{a:.0f}/anno {v:.4f}×"
                for a, v in zip(d["per_anno"], d["curve"][costo])
            )
            print(f"  costo {etichetta}: {valori}")
