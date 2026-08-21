"""Cap. analisi tecnica — La regola che ha vinto, passata al setaccio.

Due controlli sulla sola regola che ha battuto il compra-e-tieni. A sinistra:
il risultato al variare del suo unico parametro — un plateau largo dice una
cosa diversa da un picco isolato. A destra: il confronto con mille posizioni
casuali che entrano ed escono lo stesso numero di volte. Nessuno dei due
controlli e' una promessa: sono i due controlli che mancano quasi sempre.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook import seed_for  # noqa: E402
from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.regole import compra_e_tieni, esegui, rottura  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-tecnica"
COSTO = 0.0012
FINESTRE = np.arange(5, 121, 5)
SCELTA = 20
N_CASUALI = 1000
DIDASCALIA = (
    "A sinistra: la regola della rottura al variare della sua unica finestra, da 5 a "
    "120 giorni. La riga orizzontale è il compra-e-tieni: undici valori su "
    "ventiquattro lo superano, e la zona buona è un altopiano largo, non un picco "
    "isolato. A destra: mille posizioni casuali che entrano ed escono lo stesso "
    "numero di volte della regola, con gli stessi costi. La regola sta al 98esimo "
    "percentile. Detta con precisione: se non ci fosse alcun vantaggio, un risultato "
    "così o migliore capiterebbe circa due volte su cento — e le regole provate "
    "erano sei."
)


def _posizione_casuale(n: int, n_operazioni: int, rng) -> np.ndarray:
    """Entra ed esce a caso, esattamente `n_operazioni` volte."""
    pos = np.zeros(n)
    punti = np.sort(rng.choice(n - 1, size=n_operazioni, replace=False))
    stato, precedente = 0.0, 0
    for i in punti:
        pos[precedente:i] = stato
        stato, precedente = 1.0 - stato, i
    pos[precedente:] = stato
    return pos


def disegna(destinazione: str = "stampa"):
    df = carica("btcusdt").sort("data")
    p = df["chiusura"].to_numpy()

    griglia = np.array([esegui(p, rottura(p, int(n)), costo=COSTO)["finale"]
                        for n in FINESTRE])
    riferimento = esegui(p, compra_e_tieni(p), costo=COSTO)["finale"]

    scelta = esegui(p, rottura(p, SCELTA), costo=COSTO)
    n_op = int(scelta["operazioni"])

    rng = np.random.default_rng(seed_for("tecnica-verifica"))
    casuali = np.array([
        esegui(p, _posizione_casuale(len(p), n_op, rng), costo=COSTO)["finale"]
        for _ in range(N_CASUALI)
    ])
    percentile = float((casuali < scelta["finale"]).mean() * 100)

    fig, (sx, dx) = plt.subplots(1, 2, figsize=(4.25, 4.25 * 0.62))

    sx.plot(FINESTRE, griglia, color="black", linewidth=1.1, marker="o", markersize=2.4)
    sx.axhline(riferimento, color="#404040", linestyle="--", linewidth=0.9)
    sx.annotate(t("compra e tieni", "buy and hold"), xy=(FINESTRE[-1], riferimento), xytext=(-2, 4),
                textcoords="offset points", fontsize=6.5, ha="right")
    sx.axvline(SCELTA, color="#8C8C8C", linestyle=":", linewidth=0.9)
    sx.set_xlabel(t("Finestra della rottura (giorni)", "Breakout window (days)"))
    sx.set_ylabel(t("Capitale finale (volte)", "Final capital (times)"))
    sx.set_yscale("log")
    # Tacche leggibili al posto della notazione esponenziale.
    sx.set_yticks([2, 5, 10, 20, 40])
    sx.set_yticklabels(["2×", "5×", "10×", "20×", "40×"])
    sx.minorticks_off()

    dx.hist(casuali, bins=40, facecolor="white", edgecolor="black", linewidth=0.6,
            hatch="///")
    # Come sopra: la verticale resta dentro il riquadro.
    dx.axvline(scelta["finale"], color="black", linewidth=1.4, ymax=0.94)
    # Il testo non ha spazio dentro l'istogramma: a mezza altezza finiva sul
    # bordo della prima barra, che e' alta quasi quanto l'asse. Si apre una
    # fascia libera alzando il limite e lo si mette li', con un filo che lo
    # collega alla riga della regola.
    dx.set_ylim(0, dx.get_ylim()[1] * 1.24)
    dx.annotate(t(f"la regola vera: {percentile:.0f}º percentile",
                   f"the real rule: {percentile:.0f}th percentile"),
                xy=(scelta["finale"], dx.get_ylim()[1] * 0.90),
                xytext=(0.98, 0.99), textcoords="axes fraction",
                fontsize=6.5, ha="right", va="top",
                arrowprops=dict(arrowstyle="->", linewidth=0.6, color="#595959"))
    dx.set_xscale("log")
    dx.set_xlabel(t("Capitale finale (volte)", "Final capital (times)"))
    dx.set_ylabel(t(f"Su {N_CASUALI} tentativi casuali", f"Out of {N_CASUALI} random trials"))
    dx.grid(axis="x", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, BTC giornaliero, costi 0,12% per operazione",
                  f"{fonte}, daily BTC, 0.12% cost per trade"), estratto)

    disegna.numeri = {
        "riferimento": riferimento,
        "scelta": scelta["finale"],
        "operazioni": n_op,
        "battono": int((griglia > riferimento).sum()),
        "totale_griglia": len(griglia),
        "mediana_griglia": float(np.median(griglia)),
        "mediana_casuale": float(np.median(casuali)),
        "percentile": percentile,
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:18s} {v}")
