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
    # che e' il minimo della fascia successiva e quindi resta valido fino a
    # **700** pagine, non a 500 — vedi `GUTTER_KDP_IN`, che e' la tabella.
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

#: Margine interno minimo richiesto da KDP, per fascia di pagine (soglia
#: superiore inclusa, valore in pollici). Sta qui e non dentro uno script
#: perche' e' una misura della gabbia, e perche' due file la citavano a memoria
#: e la citavano sbagliata: sopra le 500 pagine il richiesto sale a 0,75", non
#: a 0,875" — quello e' il gradino delle 700. Con `inner` a 0,75" il libro
#: resta conforme fino a 700 pagine.
GUTTER_KDP_IN = ((150, 0.375), (300, 0.5), (500, 0.625), (700, 0.75), (828, 0.875))

#: Oltre questo numero di pagine KDP non stampa questo formato.
PAGINE_MASSIME_KDP = 828


def gutter_richiesto(pagine: int) -> float:
    """Il margine interno minimo che KDP chiede per quel numero di pagine."""
    for soglia, valore in GUTTER_KDP_IN:
        if pagine <= soglia:
            return valore
    raise ValueError(f"{pagine} pagine: oltre il massimo KDP di {PAGINE_MASSIME_KDP}")


#: Requisiti KDP che vincolano il disegno delle figure.
KDP_MIN_LINEWIDTH_PT = 0.75   # tratti piu' sottili spariscono in stampa
KDP_MIN_FONTSIZE_PT = 7.0     # corpo minimo ammesso
KDP_MIN_GRAY_FILL = 0.10      # riempimenti sotto il 10% non si vedono
KDP_MIN_DPI = 300

#: Corpo effettivo delle etichette nelle figure, e perche' non e' 7,0.
#:
#: `savefig.bbox = "tight"` ritaglia al contenuto e poi aggiunge `pad_inches`
#: per lato: il PNG esce largo 4,30" mentre il blocco testo ne misura 4,25.
#: LaTeX lo rimpicciolisce del fattore 0,9885 per farlo stare in gabbia, e
#: un'etichetta composta a 7,0 pt finisce stampata a 6,92 — sotto il minimo
#: che KDP dichiara. Misurato sul PDF: 2.580 px a 607 ppi effettivi.
#:
#: Si compone quindi a 7,2 pt, che dopo la riduzione valgono 7,12 pt in pagina.
#: E' la scelta meno invasiva: togliere il `tight` significherebbe rifare il
#: margine interno di tutte e 43 le figure, con il rischio di tagliare le
#: etichette ai bordi, per guadagnare un decimo di punto.
CORPO_ETICHETTE_PT = 7.2


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
