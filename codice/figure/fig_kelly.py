"""Cap. 20 — Quanto rischiare: la curva che sale, tocca la vetta e crolla.

Con un vantaggio reale esiste una frazione del capitale che massimizza la
crescita di lungo periodo. Sopra quella frazione la crescita non aumenta:
diminuisce, e oltre una certa soglia diventa distruzione garantita.
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
from cvbook.stile import firma, tacca  # noqa: E402

CAPITOLO = "sec-cap-20"
P_VINCITA = 0.55
RAPPORTO = 1.0
OPERAZIONI = 500
CAMPIONI = 3000
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Simulazione di un gioco con un vantaggio reale: si vince il 55% delle "
    "volte, guadagnando quanto si rischia. A sinistra, capitale mediano dopo "
    "500 operazioni al variare della frazione di capitale rischiata ogni "
    "volta. La crescita è massima attorno al 10%: rischiare di più non "
    "aumenta il risultato, lo riduce, e già oltre il 20% il capitale mediano "
    "finisce sotto quello di partenza — pur avendo il vantaggio. Il risultato "
    "mediano scende in modo simile da entrambi i lati del massimo: 6,5 volte "
    "al 5% e 6,5 al 15%. A destra, la probabilità di ritrovarsi con meno di "
    "un quinto del capitale iniziale — ed è questa a esplodere da un lato "
    "solo."
)


def disegna(destinazione: str = "stampa"):
    rng = np.random.default_rng(seed_for("kelly"))
    esiti = rng.random((CAMPIONI, OPERAZIONI)) < P_VINCITA
    frazioni = np.arange(0.01, 0.61, 0.01)

    # DUE DEFINIZIONI DI ROVINA, ed e' voluto che siano diverse.
    # Qui si misura dove si ARRIVA: la probabilita' di ritrovarsi a fine
    # partita con meno di un quinto del capitale, che e' la domanda del
    # capitolo e quella che l'asse dichiara. `metriche.rischio_di_rovina`
    # misura un'altra cosa — se il capitale e' MAI sceso sotto la soglia lungo
    # il percorso — che e' la definizione giusta quando la rovina e' un evento
    # assorbente, cioe' quando sotto quella soglia si smette di giocare. Le due
    # rispondono a domande diverse e la seconda da' numeri piu' alti: usare
    # quella qui cambierebbe le quattro cifre che il capitolo stampa.
    mediane, rovine = [], []
    for f in frazioni:
        passi = np.where(esiti, 1 + f * RAPPORTO, 1 - f)
        curve = np.cumprod(passi, axis=1)
        mediane.append(np.median(curve[:, -1]))
        rovine.append((curve[:, -1] < 0.2).mean() * 100)

    kelly = P_VINCITA - (1 - P_VINCITA) / RAPPORTO

    fig, (sx, dx) = plt.subplots(1, 2, figsize=figsize("media"))

    sx.plot(frazioni * 100, mediane, color="black", linewidth=1.3)
    sx.axhline(1.0, color="#8C8C8C", linestyle=":", linewidth=0.9)
    # La riga a quota 1 e' il confine fra guadagnare e perdere: senza etichetta
    # sembrava una linea di griglia qualunque.
    sx.text(0.985, 1.0, t("capitale iniziale", "starting capital"),
            transform=sx.get_yaxis_transform(), fontsize=6, color="#595959",
            ha="right", va="bottom")
    sx.axvline(kelly * 100, color="#595959", linestyle="--", linewidth=0.9)
    sx.annotate(t(f"massimo teorico a {kelly * 100:.0f}%", f"theoretical maximum at {kelly * 100:.0f}%"),
                xy=(kelly * 100, max(mediane)),
                xytext=(0.97, 0.93), textcoords="axes fraction", fontsize=6.5,
                ha="right", va="center",
                arrowprops=dict(arrowstyle="->", linewidth=0.6, color="#595959"))
    sx.set_yscale("log")
    # Oltre un certo punto la mediana crolla di trenta ordini di grandezza: se
    # si lascia l'asse libero, tutta la parte leggibile si schiaccia in cima.
    # Nove decadi erano ancora troppe — la zona che il capitolo commenta, fra
    # 0,1x e 12x, restava compressa nel quinto superiore del riquadro. Si taglia
    # a quattro decadi, che arrivano appena oltre il 30%, e si dice che sotto la
    # curva esce dal grafico.
    sx.set_ylim(1e-4, max(mediane) * 3)
    # «sotto questo punto» non indicava nessun punto: adesso l'etichetta dice
    # a quale frazione la curva esce, e quel numero lo calcola il codice.
    esce = frazioni[np.argmax(np.array(mediane) < 1e-4)] * 100
    sx.text(0.98, 0.02,
            t(f"oltre il {esce:.0f}% esce dal grafico", f"beyond {esce:.0f}% it falls off the chart"),
            transform=sx.transAxes, fontsize=6, ha="right", va="bottom",
            color="#595959",
            bbox=dict(boxstyle="square,pad=0.15", facecolor="white",
                      edgecolor="none"))
    # Tacche in multipli invece che in notazione scientifica: «10⁻³» e' una
    # barriera gratuita per il lettore a cui questo libro parla.
    sx.set_yticks([1e-4, 1e-3, 1e-2, 1e-1, 1, 10])
    sx.set_yticklabels([tacca(v, "×") for v in (1e-4, 1e-3, 1e-2, 1e-1, 1, 10)])
    sx.grid(which="minor", visible=False)
    sx.set_xlabel(t("Frazione di capitale rischiata (%)", "Fraction of capital risked (%)"))
    sx.set_ylabel(t("Capitale mediano dopo 500 operazioni", "Median capital after 500 trades"))

    dx.plot(frazioni * 100, rovine, color="black", linewidth=1.3)
    dx.axvline(kelly * 100, color="#595959", linestyle="--", linewidth=0.9)
    dx.set_xlabel(t("Frazione di capitale rischiata (%)", "Fraction of capital risked (%)"))
    dx.set_ylabel(t("Probabilità di perdere l'80% (%)", "Probability of losing 80% (%)"))
    dx.set_ylim(0, 100)

    # La firma diceva «vantaggio reale del 5%», che e' l'eccesso sul 50% di
    # frequenza di vittoria e non il vantaggio: con p=0,55 e vincita pari alla
    # posta il valore atteso per operazione e' il 10% di quanto si rischia, ed e'
    # anche il massimo della curva. Si dichiara la frequenza, che e' il dato
    # della simulazione e non ha bisogno di essere interpretato.
    firma(fig, t("simulazione con frequenza di vittoria del 55%, seme fisso",
                  "simulation with a 55% win rate, fixed seed"), "—")
    return fig
