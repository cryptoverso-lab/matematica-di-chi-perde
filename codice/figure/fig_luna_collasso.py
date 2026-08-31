"""Cap. 5 — LUNA, maggio 2022: nove giorni.

Scala logaritmica, perche' su scala lineare il crollo non e' rappresentabile:
la caduta attraversa cinque ordini di grandezza e l'ultimo tratto sarebbe
indistinguibile dallo zero.

LA SERIE SI FERMA AL 13 MAGGIO 2022, ED E' IL PUNTO PIU' IMPORTANTE DI QUESTO
FILE. Nei dump di Binance il simbolo LUNAUSDT ha un buco dal 14 al 30 maggio
2022 e poi riprende a 8,87 dollari: non e' una risalita, e' un altro token —
LUNA 2.0, listato a fine maggio sotto lo stesso ticker. Disegnare la serie per
intero produceva una retta diagonale che risaliva da 0,00005 a quasi 9 dollari
e si stabilizzava li': in un capitolo intitolato «il cimitero dei token», il
grafico mostrava una resurrezione. Era anche, alla lettera, l'errore che il
capitolo sui dati che mentono insegna a cercare — due strumenti diversi uniti
dallo stesso identificativo. Si taglia al giorno in cui il token originale
smette di essere scambiato, e la discontinuita' viene dichiarata in pagina.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import DISCONTINUITA, carica_strumento, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.stile import date_italiane, firma, tacca  # noqa: E402

CAPITOLO = "sec-cap-05"
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Prezzo giornaliero di chiusura di LUNA dal 1° aprile al 13 maggio 2022, "
    "scala logaritmica: ogni tacca vale un fattore cento. Dal massimo di 116 "
    "dollari del 4 aprile agli 0,00005 dollari del 13 maggio. Il 5 maggio "
    "valeva ancora 82 dollari: otto giorni dopo ne valeva 0,00005. La serie "
    "finisce lì perché lì finisce il token: dal 31 maggio lo stesso "
    "identificativo, sullo stesso mercato, quota un'altra cosa — un progetto "
    "nuovo lanciato dopo il crollo. Unire i due tratti disegnerebbe una "
    "risalita che nessuno ha vissuto. Su scala lineare questo grafico sarebbe "
    "una linea verticale seguita da una riga piatta a zero — ed è esattamente "
    "così che i crolli appaiono a chi li guarda mentre accadono."
)


#: Ultimo giorno in cui LUNAUSDT quota il token originale. Non si scrive qui: si
#: legge dal registro dei dati, che e' l'unico posto in cui quella data vive —
#: cosi' la figura, il paniere della sopravvivenza e il quaderno del capitolo si
#: fermano tutti nello stesso punto senza doverselo ricordare a vicenda.
ULTIMO_GIORNO = DISCONTINUITA["lunausdt"]


def disegna(destinazione: str = "stampa"):
    serie = carica_strumento("lunausdt")
    df = serie.filter(serie["data"] >= dt.date(2022, 4, 1))
    date = df["data"].to_list()
    prezzi = df["chiusura"].to_numpy()

    fig, ax = plt.subplots()
    ax.plot(date, prezzi, color="black", linewidth=1.2)
    ax.set_yscale("log")

    # Il punto del massimo sta a ridosso del bordo superiore: la sua etichetta
    # va scritta **sotto**, dove il riquadro e' vuoto, altrimenti esce dal
    # grafico. Le altre tre vanno sopra, come prima.
    # Ogni etichetta va dalla parte in cui il tracciato non passa: il massimo
    # e' a ridosso del bordo superiore, quindi la sua scritta sta sotto; il
    # minimo ha la risalita subito a destra, quindi la sua sta sotto e centrata.
    tappe = [
        (dt.date(2022, 4, 4), t("massimo\n116 $", "peak\n$116"), (6, -6), "left", "top"),
        (dt.date(2022, 5, 9), t("30 $", "$30"), (6, 6), "left", "bottom"),
        (dt.date(2022, 5, 11), t(f"{tacca(1.08)} $", f"${tacca(1.08)}"),
         (6, 6), "left", "bottom"),
        (dt.date(2022, 5, 13), t(f"{tacca(0.00005)} $", f"${tacca(0.00005)}"),
         (10, -1), "left", "center"),
    ]
    for giorno, testo, scarto, orizz, vert in tappe:
        i = date.index(giorno)
        ax.plot([giorno], [prezzi[i]], marker="o", markersize=3.2, color="black")
        ax.annotate(
            testo,
            xy=(giorno, prezzi[i]),
            xytext=scarto,
            textcoords="offset points",
            fontsize=6.5,
            linespacing=1.3,
            ha=orizz,
            va=vert,
        )

    # La serie si ferma qui, e il grafico lo dice: senza questa riga il lettore
    # legge un troncamento come una fine dei dati, che non e'.
    ax.text(
        0.03, 0.24,
        t("la serie si ferma il 13 maggio:\ndal 31 lo stesso simbolo\nquota un altro token",
          "the series stops on 13 May:\nfrom the 31st the same ticker\nquotes a different token"),
        transform=ax.transAxes,
        fontsize=6.5,
        linespacing=1.4,
        ha="left",
        va="top",
        color="#595959",
    )

    ax.set_ylabel(t("Prezzo in dollari (scala logaritmica)", "Price in dollars (log scale)"))
    ax.set_yticks([1e-4, 1e-2, 1, 100])
    ax.set_yticklabels([tacca(v) for v in (1e-4, 1e-2, 1, 100)])
    ax.tick_params(axis="x", labelrotation=0)
    ax.grid(which="minor", visible=False)
    date_italiane(ax, ogni_giorni=7)

    fonte, estratto = citazione("lunausdt")
    firma(fig, t(f"{fonte}, LUNAUSDT giornaliero", f"{fonte}, daily LUNAUSDT"), estratto)
    return fig
