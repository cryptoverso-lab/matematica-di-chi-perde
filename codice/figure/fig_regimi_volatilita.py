"""Cap. regimi — La volatilita' non e' una costante: e' una serie storica.

Deviazione standard annualizzata su finestre mobili di trenta giorni. Il valore
non oscilla attorno a una media: sta a lungo basso, poi sale e resta alto. E'
il raggruppamento della volatilita', ed e' il motivo per cui "la volatilita'
storica" e' un numero che descrive un mercato che quasi mai e' quello in cui
ti trovi adesso.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.metriche import GIORNI_ANNO, rendimenti  # noqa: E402
from cvbook.stile import firma, num  # noqa: E402

CAPITOLO = "sec-cap-regimi"
FINESTRA = 30
DIDASCALIA = (
    "Volatilità annualizzata di Bitcoin su finestre mobili di trenta giorni. La "
    "riga tratteggiata è la media dell'intero periodo, il numero che tutti "
    "chiamano \"la volatilità storica\". Il mercato passa poco tempo lì vicino: "
    "sta a lungo sotto, poi sale e resta sopra per mesi. Le bande grigie segnano i "
    "periodi in cui la volatilità è oltre il valore superato solo un quarto delle "
    "volte. Un rischio dimensionato sulla media è troppo alto metà del tempo e "
    "troppo basso l'altra metà."
)


def _serie():
    df = carica("btcusdt").sort("data")
    prezzi = df["chiusura"].to_numpy()
    date = df["data"].to_list()[1:]
    r = rendimenti(prezzi)
    return date, r


def volatilita_mobile(r: np.ndarray, finestra: int = FINESTRA) -> np.ndarray:
    """Deviazione standard annualizzata, causale: usa solo il passato."""
    return np.array([
        np.std(r[i - finestra:i], ddof=1) * np.sqrt(GIORNI_ANNO)
        for i in range(finestra, len(r) + 1)
    ])


def disegna(destinazione: str = "stampa"):
    date, r = _serie()
    vol = volatilita_mobile(r)
    date_v = date[FINESTRA - 1:]

    media = float(vol.mean())
    alta = float(np.percentile(vol, 75))
    bassa = float(np.percentile(vol, 25))

    fig, ax = plt.subplots()
    ax.fill_between(date_v, 0, 1, where=vol > alta, transform=ax.get_xaxis_transform(),
                    color="#E0E0E0", linewidth=0)
    ax.plot(date_v, vol * 100, color="black", linewidth=0.9)
    ax.axhline(media * 100, color="#404040", linestyle="--", linewidth=0.9)

    # Le due chiavi di lettura stanno in un blocco solo, nella fascia sopra il
    # massimo della serie. Appoggiare l'etichetta della media alla sua riga
    # non funziona su questa figura: la curva quella quota la attraversa
    # decine di volte, e ovunque la si metta finisce sotto il tracciato — con
    # il riquadro bianco che ne cancella un pezzo, senza il riquadro che la
    # rende illeggibile. Qui non copre niente.
    ax.text(0.015, 0.97,
            t(
                f"tratteggio: media di periodo, {num(media * 100)}%\n"
                f"grigio: sopra il {alta * 100:.0f}% (un quarto dei giorni)",
                f"dashed: period average, {num(media * 100)}%\n"
                f"grey: above {alta * 100:.0f}% (a quarter of the days)",
            ),
            transform=ax.transAxes, fontsize=6.5, linespacing=1.35, va="top")

    ax.set_ylabel(t("Volatilità annualizzata (%)", "Annualized volatility (%)"))
    # Spazio in cima per il blocco di testo: senza, finisce sui picchi del 2018.
    ax.set_ylim(0, float(vol.max()) * 132)
    fig.autofmt_xdate(rotation=0, ha="center")

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, chiusure giornaliere", f"{fonte}, daily closes"), estratto)

    disegna.numeri = {
        "media": media,
        "minimo": float(vol.min()),
        "massimo": float(vol.max()),
        "quartile_alto": alta,
        "quartile_basso": bassa,
        "rapporto": float(vol.max() / vol.min()),
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:16s} {v:.4f}")
