"""Gabbia tipografica — unica fonte di verità per tutte le misure del libro.

Da qui discendono: il `geometry` del PDF, la larghezza di ogni figura e i
controlli automatici pre-upload. Nessun numero di pagina o di figura va
scritto altrove: se il formato cambia, cambia solo questo file.

Formato deciso il 2026-08-16: KDP paperback 5,5" x 8,5", fascia 301-500 pagine.
"""

from dataclasses import dataclass

PT_PER_IN = 72.0


@dataclass(frozen=True)
class Gabbia:
    """Misure in pollici. I nomi seguono la terminologia KDP."""

    trim_w: float = 5.5
    trim_h: float = 8.5
    # Fascia 301-500 pagine: gutter minimo richiesto 0,625". Si adotta 0,75",
    # valido fino a 500 pagine e piu' comodo alla lettura su dorso incollato.
    inner: float = 0.75
    outer: float = 0.5
    top: float = 0.75
    bottom: float = 0.75

    @property
    def text_w(self) -> float:
        """Larghezza del blocco testo: la misura da cui dipende ogni figura."""
        return self.trim_w - self.inner - self.outer

    @property
    def text_h(self) -> float:
        return self.trim_h - self.top - self.bottom

    @property
    def page_pt(self) -> tuple[float, float]:
        """Dimensione pagina in punti: quello che deve riportare `pdfinfo`."""
        return (self.trim_w * PT_PER_IN, self.trim_h * PT_PER_IN)


GABBIA = Gabbia()

#: Larghezza di ogni figura del libro. Nessuna figura e' piu' larga di cosi'.
FIG_W = GABBIA.text_w

#: Altezze standard. Tre sole taglie: uniformita' visiva e impaginazione prevedibile.
FIG_H = {
    "bassa": FIG_W * 0.42,   # serie singola, andamento
    "media": FIG_W * 0.62,   # taglia di default (proporzione aurea)
    "alta": FIG_W * 0.85,    # distribuzioni, matrici, pannelli multipli
}

#: Requisiti KDP che vincolano il disegno delle figure.
KDP_MIN_LINEWIDTH_PT = 0.75   # tratti piu' sottili spariscono in stampa
KDP_MIN_FONTSIZE_PT = 7.0     # corpo minimo ammesso
KDP_MIN_GRAY_FILL = 0.10      # riempimenti sotto il 10% non si vedono
KDP_MIN_DPI = 300


def figsize(taglia: str = "media") -> tuple[float, float]:
    """Dimensione figura in pollici, sempre a piena larghezza del blocco testo."""
    if taglia not in FIG_H:
        raise ValueError(f"taglia sconosciuta: {taglia!r} — usa {sorted(FIG_H)}")
    return (FIG_W, FIG_H[taglia])


if __name__ == "__main__":
    g = GABBIA
    print(f"trim          {g.trim_w}in x {g.trim_h}in")
    print(f"pagina PDF    {g.page_pt[0]:.0f} x {g.page_pt[1]:.0f} pts")
    print(f"blocco testo  {g.text_w}in x {g.text_h}in")
    print(f"figura        {FIG_W}in di larghezza")
    for k, v in FIG_H.items():
        print(f"  {k:6s} {FIG_W:.2f} x {v:.2f} in")
